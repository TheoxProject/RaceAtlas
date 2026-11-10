from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from raceatlas.ffc import parse_race
from raceatlas.sync.fingerprint import fingerprint, observation_facts

HTML = (Path(__file__).resolve().parents[2] / "fixtures/ffc/race.synthetic.html").read_text(
    encoding="utf-8"
)
URL = "https://competitions.ffc.fr/calendrier/competition/2027/SYNTHETIC001/fictive/"


def observation(html=HTML, day=10):
    return parse_race(html, source_url=URL, checked_at=datetime(2026, 11, day, tzinfo=timezone.utc))


def test_check_times_tokens_slug_and_display_whitespace_are_not_business_revisions():
    first = observation()
    second = observation(
        HTML.replace("Course fictive des collines", "Course   fictive des collines"), 11
    )
    assert first.scopes[0].token != second.scopes[0].token
    assert first.scopes[0].rules[0].evidence_id != second.scopes[0].rules[0].evidence_id
    assert fingerprint(observation_facts(first)) == fingerprint(observation_facts(second))


def test_correlated_restrictions_and_scope_reorder_are_business_facts():
    first = observation()
    changed = observation(HTML.replace("<dd>Hommes</dd>", "<dd>Femmes</dd>"))
    assert fingerprint(observation_facts(first)) != fingerprint(observation_facts(changed))
    reordered = replace(first, scopes=tuple(reversed(first.scopes)))
    assert fingerprint(observation_facts(first)) != fingerprint(observation_facts(reordered))
