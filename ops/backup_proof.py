"""Explicit local synthetic PG17 restore exercise; never a production backup tool."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from ops.backup_common import ROOT, ProofError, guard_path, require

CLUSTER = ROOT / ".local-tools" / "pgdata-lot2-native"
MIGRATION = "b806e44f7901"


@dataclass(frozen=True)
class ProofConfig:
    pg_bin: Path
    expected_data_directory: Path
    source_name: str
    restore_name: str
    output_directory: Path
    host: str = "127.0.0.1"
    hostaddr: str = "127.0.0.1"
    port: int = 55434
    user: str = "raceatlas_local"


def validate_config(config, environ):
    # psycopg/libpq, not just child CLIs, must be protected from ambient settings.
    require(not any(key.upper().startswith("PG") for key in environ), "ambient_libpq")
    require(config.host == config.hostaddr == "127.0.0.1", "loopback_required")
    require(config.port == 55434 and config.user == "raceatlas_local", "local_identity")
    match = re.fullmatch(r"raceatlas_backup_src_([a-f0-9]{16})", config.source_name)
    require(match is not None, "source_namespace")
    nonce = match.group(1)
    require(config.restore_name == "raceatlas_backup_dst_" + nonce, "restore_namespace")
    expected_output = ROOT / ".local-tools" / "backup-proof" / nonce
    for path in (
        config.output_directory,
        expected_output,
        config.expected_data_directory,
        CLUSTER,
        config.pg_bin,
    ):
        guard_path(path)
    require(config.expected_data_directory.resolve() == CLUSTER.resolve(), "cluster_path")
    require(config.output_directory.resolve() == expected_output.resolve(), "output_path")
    require(not config.output_directory.exists(), "existing_output")
    require(config.expected_data_directory.is_dir() and config.pg_bin.is_dir(), "missing_path")
    for name in ("pg_dump", "pg_restore"):
        binary = executable(config, name)
        require(binary.is_file() and not binary.is_symlink(), "missing_binary")
    return nonce


def executable(config, name):
    path = config.pg_bin / (name + (".exe" if os.name == "nt" else ""))
    guard_path(path)
    return path


def child_environment(environ, config, passfile, database):
    system_keys = {
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "WINDIR",
        "SYSTEMDRIVE",
        "COMSPEC",
        "TEMP",
        "TMP",
        "HOME",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
        "LANG",
        "LC_ALL",
    }
    result = {key: value for key, value in environ.items() if key.upper() in system_keys}
    result.update(
        PGHOST=config.host,
        PGHOSTADDR=config.hostaddr,
        PGPORT=str(config.port),
        PGUSER=config.user,
        PGDATABASE=database,
        PGPASSFILE=str(passfile),
        PGSSLMODE="disable",
        PGGSSENCMODE="disable",
        PGCONNECT_TIMEOUT="3",
        PGOPTIONS="",
    )
    return result


def connection_parameters(config, passfile, database="postgres"):
    guard_path(passfile, "worker_passfile")
    return dict(
        host=config.host,
        hostaddr=config.hostaddr,
        port=config.port,
        user=config.user,
        dbname=database,
        passfile=str(passfile),
        sslmode="disable",
        gssencmode="disable",
        connect_timeout=3,
        options="",
    )


def database_url(config, passfile, database):
    params = connection_parameters(config, passfile, database)
    return URL.create(
        "postgresql+psycopg",
        username=params.pop("user"),
        host=params.pop("host"),
        port=params.pop("port"),
        database=params.pop("dbname"),
        query={key: str(value) for key, value in params.items()},
    )


def command(arguments, env, code, *, timeout=120, input_data=None, allow_failure=False):
    result = subprocess.run(
        [str(arg) for arg in arguments],
        cwd=ROOT,
        env=env,
        capture_output=True,
        input=input_data,
        timeout=timeout,
        check=False,
    )
    require(allow_failure or result.returncode == 0, code)
    return (result.returncode, result.stdout) if allow_failure else result.stdout


def validate_server(connection, config, *, database_name="postgres"):
    version, directory, user, database, address, port = connection.execute(
        "SELECT current_setting('server_version_num'), current_setting('data_directory'), "
        "current_user, current_database(), host(inet_server_addr()), inet_server_port()"
    ).fetchone()
    require(170000 <= int(version) < 180000, "server_version")
    guard_path(Path(directory), "server_cluster")
    guard_path(config.expected_data_directory, "server_cluster")
    require(Path(directory).resolve() == config.expected_data_directory.resolve(), "server_cluster")
    require(user == config.user and database == database_name, "server_identity")
    require(address == "127.0.0.1" and port == config.port, "server_endpoint")
    return int(version)


def require_absent(connection, names):
    existing = connection.execute(
        "SELECT datname FROM pg_database WHERE datname = ANY(%s)", (list(names),)
    ).fetchall()
    require(not existing, "existing_database")


def create_database(connection, config, name):
    validate_server(connection, config)
    require_absent(connection, (name,))
    connection.execute(
        sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8'").format(
            sql.Identifier(name)
        )
    )


def validate_target(config, passfile, name):
    with psycopg.connect(**connection_parameters(config, passfile, name)) as connection:
        validate_server(connection, config, database_name=name)


def dump_arguments(config, archive):
    return [
        executable(config, "pg_dump"),
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--file",
        archive,
    ]


def restore_arguments(config, archive):
    return [
        executable(config, "pg_restore"),
        "--exit-on-error",
        "--single-transaction",
        "--no-owner",
        "--no-privileges",
        "--dbname",
        config.restore_name,
        archive,
    ]


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )


def tool_identity(env):
    source_sha = (
        command(["git", "rev-parse", "HEAD"], env, "source_identity").decode("ascii").strip()
    )
    require(re.fullmatch("[a-f0-9]{40}", source_sha) is not None, "source_identity")
    return dict(
        source_sha=source_sha,
        tool_sha256=hashlib.sha256(
            (ROOT / "ops/backup_proof.py").read_bytes()
            + (ROOT / "ops/backup_fixture.py").read_bytes()
            + (ROOT / "ops/backup_common.py").read_bytes()
        ).hexdigest(),
    )


def manifest(engine):
    from raceatlas.models import Base

    with engine.connect() as connection:
        connection.exec_driver_sql("SET TIME ZONE 'UTC'")
        tables = {}
        for name in sorted([*Base.metadata.tables, "alembic_version"]):
            # Names are internal model metadata, never operator text.
            rows = (
                connection.exec_driver_sql(
                    f'SELECT to_jsonb(t) FROM "{name}" t ORDER BY to_jsonb(t)::text'
                )
                .scalars()
                .all()
            )
            tables[name] = dict(count=len(rows), sha256=hashlib.sha256(canonical(rows)).hexdigest())
        constraints = connection.exec_driver_sql(
            "SELECT conrelid::regclass::text, conname, contype, conkey, "
            "NULLIF(confrelid,0)::regclass::text, confkey, confupdtype, confdeltype, "
            "confmatchtype, condeferrable, condeferred, convalidated, connoinherit "
            "FROM pg_constraint WHERE connamespace='public'::regnamespace ORDER BY 1,2"
        ).all()
        sequences = connection.exec_driver_sql(
            "SELECT sequencename,last_value FROM pg_sequences WHERE schemaname='public' ORDER BY 1"
        ).all()
        require(
            connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one()
            == MIGRATION,
            "migration_version",
        )
        return dict(
            tables=tables,
            constraints=[list(row) for row in constraints],
            sequences=[list(row) for row in sequences],
        )


def write_constraint_definitions(engine, path):
    # PostgreSQL re-parses dump DDL and may move text[] casts onto ARRAY elements.
    # Preserve both deparses for review; do not claim byte equality proves semantics.
    guard_path(path)
    with engine.connect() as connection:
        rows = connection.exec_driver_sql(
            "SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid) "
            "FROM pg_constraint WHERE connamespace='public'::regnamespace ORDER BY 1,2"
        ).all()
    path.write_bytes(canonical([list(row) for row in rows]))
    return rows


def compare_manifests(before, after):
    require(before == after, "manifest_mismatch")


def verify_archive(archive, digest):
    guard_path(archive, "archive_path")
    require(archive.is_file() and not archive.is_symlink(), "archive_path")
    require(hashlib.sha256(archive.read_bytes()).hexdigest() == digest, "archive_changed")


def verify_http_worker(config, passfile, fixture):
    env = child_environment(os.environ, config, passfile, config.restore_name)
    env.update(
        DATABASE_URL=database_url(config, passfile, config.restore_name).render_as_string(
            hide_password=False
        ),
        RACEATLAS_ENV="test",
    )
    exit_code, raw = command(
        [sys.executable, "-m", "ops.backup_fixture"],
        env,
        "http_worker",
        input_data=canonical(fixture),
        allow_failure=True,
    )
    require(len(raw) <= 4096, "http_worker_response")
    result = json.loads(raw)
    require(isinstance(result, dict), "http_worker_response")
    if result.get("result") != "passed":
        code = result.get("code", "failed")
        require(
            isinstance(code, str) and re.fullmatch("[a-z_]{1,64}", code), "http_worker_response"
        )
        raise ProofError("http_worker_" + code)
    require(exit_code == 0, "http_worker_exit")
    count = result.get("http_assertions")
    require(type(count) is int and count >= 21, "http_worker_assertions")
    return count


def run_proof(config):
    from ops.backup_fixture import (
        build_fixture,
        verify_check_differences,
        verify_constraints,
    )

    phase = "validation"
    report = {"result": "failed", "phase": phase}
    source_engine = restore_engine = None
    output_created = False
    try:
        validate_config(config, os.environ)
        config.output_directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        output_created = True
        passfile = config.output_directory / "empty.pgpass"
        guard_path(passfile, "worker_passfile")
        with passfile.open("x", encoding="utf-8"):
            pass
        passfile.chmod(0o600)
        env = child_environment(os.environ, config, passfile, "postgres")
        report.update(tool_identity(env))
        phase = "preflight"
        for binary in ("pg_dump", "pg_restore"):
            value = (
                command([executable(config, binary), "--version"], env, "client_version")
                .decode("ascii", errors="strict")
                .strip()
            )
            require(
                re.fullmatch(r"pg_(?:dump|restore) \(PostgreSQL\) 17\.\d+(?:\D.*)?", value)
                is not None,
                "client_version",
            )
            report[binary] = value
        with psycopg.connect(
            **connection_parameters(config, passfile), autocommit=True
        ) as maintenance:
            report["server_version_num"] = validate_server(maintenance, config)
            require_absent(maintenance, (config.source_name, config.restore_name))
            phase = "create_source"
            create_database(maintenance, config, config.source_name)
            phase = "migration_fixture"
            source_url = database_url(config, passfile, config.source_name)
            validate_target(config, passfile, config.source_name)
            migrate_env = child_environment(os.environ, config, passfile, config.source_name)
            migrate_env.update(
                DATABASE_URL=source_url.render_as_string(hide_password=False), RACEATLAS_ENV="test"
            )
            command([sys.executable, "-m", "alembic", "upgrade", "head"], migrate_env, "migration")
            source_engine = create_engine(source_url)
            fixture = build_fixture(source_engine)
            before = manifest(source_engine)
            source_definitions = write_constraint_definitions(
                source_engine, config.output_directory / "constraints-source.json"
            )
            (config.output_directory / "manifest-source.json").write_bytes(canonical(before))
            phase = "dump"
            archive = config.output_directory / "synthetic.dump"
            guard_path(archive, "archive_path")
            command(dump_arguments(config, archive), migrate_env, "dump")
            report["archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
            phase = "create_restore"
            create_database(maintenance, config, config.restore_name)
            phase = "restore"
            restore_env = child_environment(os.environ, config, passfile, config.restore_name)
            verify_archive(archive, report["archive_sha256"])
            command(restore_arguments(config, archive), restore_env, "restore")
        restore_engine = create_engine(database_url(config, passfile, config.restore_name))
        phase = "manifest"
        validate_target(config, passfile, config.restore_name)
        restored = manifest(restore_engine)
        restored_definitions = write_constraint_definitions(
            restore_engine, config.output_directory / "constraints-restored.json"
        )
        (config.output_directory / "manifest-restored.json").write_bytes(canonical(restored))
        compare_manifests(before, restored)
        report.update(
            verify_check_differences(
                source_engine, restore_engine, source_definitions, restored_definitions
            )
        )
        report["manifest_sha256"] = hashlib.sha256(canonical(restored)).hexdigest()
        report["tables_verified"] = len(restored["tables"])
        phase = "constraints"
        report["constraints_verified"] = verify_constraints(restore_engine, fixture)
        require(manifest(restore_engine) == before, "constraint_rollback")
        phase = "http"
        report["http_assertions"] = verify_http_worker(config, passfile, fixture)
        report.update(result="passed", phase="complete", migration=MIGRATION)
    except Exception as error:
        # No raw exception, driver stderr, DSN, password, mail or token crosses here.
        report.update(
            phase=phase,
            code=str(error) if isinstance(error, ProofError) else "operation_failed",
            error_type=type(error).__name__,
        )
    finally:
        for engine in (source_engine, restore_engine):
            if engine is not None:
                engine.dispose()
    if output_created:
        # Only write after validation created the directory, never into a rejected path.
        if (config.output_directory / "empty.pgpass").is_file():
            (config.output_directory / "report.json").write_bytes(canonical(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "pg-bin",
        "expected-data-directory",
        "source-name",
        "restore-name",
        "output-directory",
    ):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--hostaddr", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55434)
    parser.add_argument("--user", default="raceatlas_local")
    args = vars(parser.parse_args())
    for name in ("pg_bin", "expected_data_directory", "output_directory"):
        args[name] = Path(args[name])
    result = run_proof(ProofConfig(**args))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
