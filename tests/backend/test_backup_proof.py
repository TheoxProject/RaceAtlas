"""Normal CI guard tests; native two-new-database proof is a separate explicit CLI."""

from dataclasses import replace
from pathlib import Path

import pytest

from ops import backup_proof as proof


@pytest.fixture
def config(tmp_path, monkeypatch):
    monkeypatch.setattr(proof, "tool_identity", lambda env: {"source_sha": "0" * 40})
    monkeypatch.setattr(proof, "ROOT", tmp_path)
    cluster = tmp_path / ".local-tools/pgdata-lot2-native"
    cluster.mkdir(parents=True)
    monkeypatch.setattr(proof, "CLUSTER", cluster)
    binaries = tmp_path / "bin"
    binaries.mkdir()
    for name in ("pg_dump", "pg_restore"):
        proof.executable(
            replace_config := proof.ProofConfig(binaries, cluster, "", "", tmp_path), name
        ).touch()
    nonce = "0123456789abcdef"
    return replace(
        replace_config,
        source_name="raceatlas_backup_src_" + nonce,
        restore_name="raceatlas_backup_dst_" + nonce,
        output_directory=tmp_path / ".local-tools/backup-proof" / nonce,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("host", "example.test"),
        ("hostaddr", "192.0.2.1"),
        ("host", "localhost"),
        ("port", 5432),
        ("user", "postgres"),
        ("source_name", "raceatlas_lot2_test"),
        ("restore_name", "raceatlas_lot2_review"),
        ("source_name", "raceatlas_backup_src_0123456789abcdef;DROP DATABASE postgres"),
        ("restore_name", "raceatlas_backup_src_0123456789abcdef"),
        ("restore_name", "raceatlas_backup_dst_ffffffffffffffff"),
    ],
)
def test_invalid_destination_fails_before_any_connection_or_creation(
    config, monkeypatch, field, value
):
    monkeypatch.setattr(proof.psycopg, "connect", lambda **kwargs: pytest.fail("Must not connect"))
    result = proof.run_proof(replace(config, **{field: value}))
    assert result["result"] == "failed" and result["phase"] == "validation"
    assert not config.output_directory.exists()


@pytest.mark.parametrize(
    "name",
    [
        "PGSERVICE",
        "PGSERVICEFILE",
        "PGHOSTADDR",
        "PGOPTIONS",
        "PGDATABASE",
        "PGPASSWORD",
        "PGPASSFILE",
        "PGAPPNAME",
        "pgservice",
    ],
)
def test_every_ambient_libpq_setting_is_rejected_without_echo(config, name):
    with pytest.raises(proof.ProofError, match="^ambient_libpq$"):
        proof.validate_config(config, {name: "synthetic-must-not-be-reflected"})


def test_existing_output_wrong_cluster_symlink_and_missing_binary_rejected(config, monkeypatch):
    assert proof.validate_config(config, {}) == "0123456789abcdef"
    with pytest.raises(proof.ProofError, match="cluster_path"):
        proof.validate_config(replace(config, expected_data_directory=config.pg_bin), {})
    config.output_directory.mkdir(parents=True)
    with pytest.raises(proof.ProofError, match="existing_output"):
        proof.validate_config(config, {})
    # No platform-specific symlink privilege or skipped Windows test required.
    monkeypatch.setattr(Path, "exists", lambda self: False)
    monkeypatch.setattr(Path, "is_symlink", lambda self: self == config.output_directory)
    with pytest.raises(proof.ProofError, match="symlink_path"):
        proof.validate_config(config, {})


def test_cli_and_psycopg_both_use_explicit_local_parameters_and_empty_passfile(config):
    passfile = config.output_directory / "empty.pgpass"
    env = proof.child_environment(
        {"PGSERVICE": "bad", "PGPASSWORD": "bad", "DATABASE_URL": "bad", "PATH": "safe"},
        config,
        passfile,
        config.source_name,
    )
    assert "PGSERVICE" not in env and "PGPASSWORD" not in env and "DATABASE_URL" not in env
    params = proof.connection_parameters(config, passfile, config.source_name)
    assert params["host"] == params["hostaddr"] == env["PGHOST"] == env["PGHOSTADDR"] == "127.0.0.1"
    assert params["passfile"] == env["PGPASSFILE"] == str(passfile)
    assert params["options"] == env["PGOPTIONS"] == ""
    assert params["sslmode"] == params["gssencmode"] == "disable"
    assert "password" not in params
    url = proof.database_url(config, passfile, config.source_name)
    assert url.query["hostaddr"] == "127.0.0.1" and url.query["passfile"] == str(passfile)


def test_dump_and_restore_argv_are_fixed_no_shell_clean_or_dsn(config):
    archive = config.output_directory / "synthetic.dump"
    dump, restore = proof.dump_arguments(config, archive), proof.restore_arguments(config, archive)
    assert dump[1:] == ["--format=custom", "--no-owner", "--no-privileges", "--file", archive]
    assert restore[1:] == [
        "--exit-on-error",
        "--single-transaction",
        "--no-owner",
        "--no-privileges",
        "--dbname",
        config.restore_name,
        archive,
    ]
    assert all(
        "--clean" not in str(arg) and "postgresql://" not in str(arg) for arg in dump + restore
    )


def test_wrong_client_version_stops_before_connect_and_redacts_output(config, monkeypatch):
    monkeypatch.setattr(proof, "command", lambda *args, **kwargs: b"pg_dump (PostgreSQL) 16.9")
    monkeypatch.setattr(proof.psycopg, "connect", lambda **kwargs: pytest.fail("Must not connect"))
    result = proof.run_proof(config)
    assert result["phase"] == "preflight" and result["code"] == "client_version"
    assert "16.9" not in str(result)


class Connection:
    def __init__(self, config, *, existing=False, **settings):
        self.row = [
            "170011",
            str(config.expected_data_directory),
            config.user,
            "postgres",
            "127.0.0.1",
            config.port,
        ]
        for key, index in {
            "version": 0,
            "directory": 1,
            "user": 2,
            "database": 3,
            "address": 4,
            "port": 5,
        }.items():
            if key in settings:
                self.row[index] = settings[key]
        self.existing, self.statements = existing, []

    def execute(self, statement, params=None):
        self.statements.append(statement)
        return self

    def fetchone(self):
        return self.row

    def fetchall(self):
        return [("existing",)] if self.existing else []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


@pytest.mark.parametrize(
    "patch",
    [
        {"version": "160000"},
        {"directory": "/other"},
        {"user": "other"},
        {"database": "other"},
        {"address": "192.0.2.1"},
        {"port": 5432},
    ],
)
def test_wrong_server_identity_stops_before_create(config, patch):
    connection = Connection(config, **patch)
    with pytest.raises(proof.ProofError):
        proof.create_database(connection, config, config.source_name)
    assert len(connection.statements) == 1


def test_existing_database_rejected_and_create_rechecks_identity_and_absence(config):
    connection = Connection(config, existing=True)
    with pytest.raises(proof.ProofError, match="existing_database"):
        proof.create_database(connection, config, config.source_name)
    assert len(connection.statements) == 2
    connection = Connection(config)
    proof.create_database(connection, config, config.source_name)
    assert len(connection.statements) == 3
    assert "host(inet_server_addr())" in connection.statements[0]
    assert config.source_name in connection.statements[-1].as_string()
    assert "IF NOT EXISTS" not in connection.statements[-1].as_string()


def test_rejected_existing_output_is_never_modified(config):
    config.output_directory.mkdir(parents=True)
    marker = config.output_directory / "empty.pgpass"
    marker.write_text("synthetic-existing-must-not-change", encoding="utf-8")
    assert proof.run_proof(config)["code"] == "existing_output"
    assert marker.read_text(encoding="utf-8") == "synthetic-existing-must-not-change"
    assert not (config.output_directory / "report.json").exists()


def test_wrong_new_source_connection_stops_before_migration_or_fixture(config, monkeypatch):
    commands, connections = [], []

    def run(arguments, *args, **kwargs):
        commands.append(arguments)
        return b"pg_dump (PostgreSQL) 17.11"

    def connect(**kwargs):
        connections.append(kwargs)
        # The second connection is meant to target the newly created source.
        # A fallback to the maintenance DB must be rejected before Alembic.
        return Connection(config)

    monkeypatch.setattr(proof, "command", run)
    monkeypatch.setattr(proof.psycopg, "connect", connect)
    result = proof.run_proof(config)
    assert result["phase"] == "migration_fixture" and result["code"] == "server_identity"
    assert len(commands) == 2 and all(args[-1] == "--version" for args in commands)
    assert [item["dbname"] for item in connections] == ["postgres", config.source_name]
