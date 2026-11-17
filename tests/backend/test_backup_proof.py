"""Normal CI guard tests; native two-new-database proof is a separate explicit CLI."""

import hashlib
import json
from contextlib import nullcontext
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

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
        {
            "PGSERVICE": "bad",
            "PGPASSWORD": "bad",
            "DATABASE_URL": "bad",
            "PATH": "safe",
            "RESEND_API_KEY": "synthetic-not-for-child",
            "AUTH_CSRF_KEY": "synthetic-parent-key",
        },
        config,
        passfile,
        config.source_name,
    )
    assert "PGSERVICE" not in env and "PGPASSWORD" not in env and "DATABASE_URL" not in env
    assert "RESEND_API_KEY" not in env and "AUTH_CSRF_KEY" not in env
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


@pytest.mark.parametrize("part", ["tables", "constraints", "sequences"])
def test_manifest_comparison_never_ignores_data_or_constraint_structure(part):
    source = {
        "tables": {"account": {"count": 2, "sha256": "a" * 64}},
        "constraints": [
            [
                "saved_entry",
                "fk_scope",
                "f",
                [3],
                "entry_scope",
                [1],
                "a",
                "r",
                "s",
                False,
                False,
                True,
                False,
            ]
        ],
        "sequences": [["scope_change_sequence_seq", 2]],
    }
    proof.compare_manifests(source, deepcopy(source))
    changed = deepcopy(source)
    if part == "tables":
        changed[part]["account"]["sha256"] = "b" * 64
    elif part == "constraints":
        changed[part][0][7] = "c"  # RESTRICT -> CASCADE must never compare equal.
    else:
        changed[part][0][1] = 1
    with pytest.raises(proof.ProofError, match="manifest_mismatch"):
        proof.compare_manifests(source, changed)


def test_archive_is_rehashed_immediately_before_restore(tmp_path):
    archive = tmp_path / "synthetic.dump"
    archive.write_bytes(b"synthetic archive created by this run")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    proof.verify_archive(archive, digest)
    archive.write_bytes(b"changed after creation")
    with pytest.raises(proof.ProofError, match="archive_changed"):
        proof.verify_archive(archive, digest)


def test_unknown_check_definition_difference_is_not_silently_accepted():
    from ops.backup_fixture import verify_check_differences

    source = [("account", "unexpected", "CHECK (1=1)")]
    restored = [("account", "unexpected", "CHECK (1=2)")]
    with pytest.raises(proof.ProofError, match="unexpected_constraint_definition"):
        verify_check_differences(None, None, source, restored)


def test_known_check_domains_are_probed_on_both_sides_and_changed_truth_fails():
    from ops.backup_fixture import verify_check_differences

    source = [("auth_challenge", "ck_auth_challenge_purpose", "source deparse")]
    restored = [("auth_challenge", "ck_auth_challenge_purpose", "restored deparse")]

    def engine(always_true=False):
        def execute(statement, params):
            if "pg_get_expr" in statement:
                value = "purpose = ANY(ARRAY['confirmation','reset'])"
            else:
                value = always_true or json.loads(params[0])["purpose"] in {"confirmation", "reset"}
            return SimpleNamespace(scalar_one=lambda: value)

        return SimpleNamespace(
            connect=lambda: nullcontext(SimpleNamespace(exec_driver_sql=execute))
        )

    result = verify_check_differences(engine(), engine(), source, restored)
    assert result["check_sql_text_match"] is False and result["check_sql_diff_count"] == 1
    assert result["check_domain_assertions"] == 6
    with pytest.raises(proof.ProofError, match="check_domain_mismatch"):
        verify_check_differences(engine(), engine(always_true=True), source, restored)


def test_invalid_enum_sentinel_fits_even_smallest_varchar_domain():
    from ops.backup_fixture import check_probes

    probes = check_probes()
    for key in (
        ("auth_admission_bucket", "ck_auth_admission_bucket_namespace"),
        ("auth_challenge", "ck_auth_challenge_purpose"),
        ("commune", "ck_commune_department"),
        ("source_record", "ck_source_record_provider"),
    ):
        values, expected = probes[key][-1]
        assert expected is False and set(values.values()) == {"!"}
        assert all(len(value) <= 2 for value in values.values())


@pytest.mark.parametrize("mode", ["correct", "wrong_url", "wrong_database"])
def test_restored_factory_target_verified_before_any_http(mode):
    from ops.backup_fixture import verify_app_database

    url = proof.URL.create("postgresql+psycopg", host="127.0.0.1", database="new_restore")
    expected = SimpleNamespace(url=url)
    if mode == "wrong_url":
        actual = SimpleNamespace(
            url=url.set(database="raceatlas_lot2_test"),
            connect=lambda: pytest.fail("Must fail before SQL"),
        )
    else:
        name = "new_restore" if mode == "correct" else "raceatlas_lot2_review"
        connection = SimpleNamespace(
            exec_driver_sql=lambda sql: SimpleNamespace(scalar_one=lambda: name)
        )
        actual = SimpleNamespace(url=url, connect=lambda: nullcontext(connection))
    app = SimpleNamespace(extensions={"database": actual})
    if mode == "correct":
        verify_app_database(app, expected)
    else:
        with pytest.raises(proof.ProofError, match="factory_database"):
            verify_app_database(app, expected)


def test_http_worker_uses_restore_environment_and_leaves_parent_untouched(config, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "synthetic-parent-must-not-be-used")
    monkeypatch.setenv("PGSERVICE", "synthetic-parent-service")
    import os

    before = dict(os.environ)
    observed = []

    def run(arguments, env, code, **kwargs):
        observed.append((arguments, env, kwargs))
        return 0, b'{"result":"passed","http_assertions":21}'

    monkeypatch.setattr(proof, "command", run)
    fixture = {"alice": "synthetic-alice", "bob": "synthetic-bob"}
    passfile = config.output_directory / "empty.pgpass"
    assert proof.verify_http_worker(config, passfile, fixture) == 21
    arguments, env, kwargs = observed[0]
    assert arguments[1:] == ["-m", "ops.backup_fixture"]
    assert "PGSERVICE" not in env and env["PGDATABASE"] == config.restore_name
    assert proof.URL.create("postgresql+psycopg").drivername in env["DATABASE_URL"]
    assert config.restore_name in env["DATABASE_URL"]
    assert json.loads(kwargs["input_data"]) == fixture and kwargs["allow_failure"]
    assert dict(os.environ) == before


@pytest.mark.parametrize(
    "exit_code,body",
    [
        (1, b'{"result":"failed","code":"restored_hash_login"}'),
        (0, b'{"result":"passed","http_assertions":0}'),
        (0, b'{"result":"passed","http_assertions":true}'),
        (1, b'{"result":"passed","http_assertions":21}'),
    ],
)
def test_failed_or_incomplete_worker_is_never_a_pass(config, monkeypatch, exit_code, body):
    monkeypatch.setattr(proof, "command", lambda *args, **kwargs: (exit_code, body))
    with pytest.raises(proof.ProofError):
        proof.verify_http_worker(config, config.output_directory / "empty.pgpass", {})


@pytest.mark.parametrize("patch", ["valid", "remote", "test_database", "ambient_service"])
def test_worker_target_guard_before_connection(config, monkeypatch, patch):
    from ops import backup_fixture

    monkeypatch.setattr(backup_fixture, "ROOT", proof.ROOT)
    config.output_directory.mkdir(parents=True)
    passfile = config.output_directory / "empty.pgpass"
    passfile.write_bytes(b"")
    url = proof.database_url(config, passfile, config.restore_name)
    env = proof.child_environment({}, config, passfile, config.restore_name)
    if patch == "remote":
        url = url.set(host="example.test")
    elif patch == "test_database":
        url = url.set(database="raceatlas_lot2_test")
    elif patch == "ambient_service":
        env["PGSERVICE"] = "untrusted"
    env.update(DATABASE_URL=url.render_as_string(hide_password=False), RACEATLAS_ENV="test")
    fixture = {"alice": "a", "bob": "b"}
    if patch == "valid":
        _, actual_passfile, actual_url = backup_fixture.worker_parameters(env, fixture)
        assert (
            actual_url
            == proof.URL.create(
                "postgresql+psycopg",
                username=url.username,
                host=url.host,
                port=url.port,
                database=url.database,
                query={k: v for k, v in url.query.items() if v != ""},
            )
            and actual_passfile == passfile
        )
    else:
        with pytest.raises(proof.ProofError, match="worker_"):
            backup_fixture.worker_parameters(env, fixture)
