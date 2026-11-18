"""Synthetic examples of the public FFC pages, without captured source HTML."""

from datetime import date, datetime, timezone
from unittest import TestCase

from raceatlas.ffc import AdapterError, WindowRequest
from raceatlas.ffc.public_2027 import parse_public_calendar, parse_public_race
from raceatlas.ffc.types import SourceKey

NOW = datetime(2026, 11, 18, tzinfo=timezone.utc)
BASE = "https://competitions.ffc.fr"
CALENDAR = f"{BASE}/calendrier/?debut=2027-01-01&nbjours=14&departement=38"
PATH = "/calendrier/competition/2027/C4100041234/course-test/"
KEY = SourceKey(2027, "C4100041234")
REQUEST = WindowRequest(date(2027, 1, 1), date(2027, 1, 14), "38")


def calendar_html(count=1, department="38", end="jeudi 14 janvier 2027"):
    return f"""
    <select id="filtreDepartementID">
      <option value="">Tous les départements</option>
      <option selected="selected" value="{department}">Département sélectionné</option>
    </select>
    <select id="filtreNombreDeJoursID"><option selected value="14">14</option></select>
    <div id="cpContent_InfoJourSelection">
      {count} compétition du vendredi 01 janvier 2027 au {end}
    </div>
    <a href="{PATH}">Course Test</a>
    <a href="{BASE}{PATH}">Répétition dans l'interface</a>
    """


def race_html(
    *labels,
    discipline="Cyclo-Cross",
    keys=("C4100041234", "2027"),
    department="Isère",
    day="samedi 09 janvier 2027",
    extra=(),
):
    facts = (
        ("N° d'épreuve", keys[0]),
        ("Saison", keys[1]),
        ("Type de compétition", "Régional"),
        ("Organisateur", "Club Test"),
        ("Durée", "2 jours"),
        *extra,
    )
    info = "".join(
        f'<div class="info-principale"><div class="titreValeur-titre">{label}</div>'
        f'<div class="titreValeur-valeur">{value}</div></div>'
        for label, value in facts
    )
    badges = "".join(f'<div class="epreuve-badge">{label}</div>' for label in labels)
    return f"""
    <div id="organisationView">
      <div id="OrganisationTitleID">
        <div class="discipline">{discipline}</div>
        <div class="date">{day}</div>
        <h1 class="titre">Course Test sans commune annoncée</h1>
        <div class="localisation"><i class="map-icon"></i>{department}</div>
      </div>
      <div id="infosPrincipales">{info}</div>
      <div id="epreuvesContenu">
        <div class="epreuve">
          <div class="epreuve-description vertical">
            <div class="vertical">
              <div class="epreuve-titre">Critères d'admissibilité</div>
              <div class="horizontal">{badges}</div>
            </div>
            <div class="vertical"><div>Engagements réservés pour : Club, Individuel</div></div>
          </div>
        </div>
      </div>
    </div>
    """


def parse_calendar(html):
    return parse_public_calendar(html, source_url=CALENDAR, checked_at=NOW, requested=REQUEST)


def parse_race(html):
    return parse_public_race(
        html,
        source_url=BASE + PATH,
        checked_at=NOW,
        expected_key=KEY,
        expected_department="38",
    )


class PublicFfcReaderTests(TestCase):
    def test_reconciles_effective_window_and_deduplicates_link(self):
        observation, links = parse_calendar(calendar_html())
        self.assertEqual(observation.status, "consistent_sample")
        self.assertEqual(observation.diagnostics, ())
        self.assertEqual(observation.effective_department, "38")
        self.assertEqual(observation.effective_start, date(2027, 1, 1))
        self.assertEqual(observation.effective_end, date(2027, 1, 14))
        self.assertEqual(observation.keys, (KEY,))
        self.assertEqual(links, {KEY: BASE + PATH})

    def test_disagreement_stays_incomplete(self):
        observation, _ = parse_calendar(calendar_html(3, "26", "mercredi 13 janvier 2027"))
        self.assertEqual(observation.status, "incomplete")
        self.assertEqual(
            {diagnostic.code for diagnostic in observation.diagnostics},
            {"window_mismatch", "department_mismatch", "count_mismatch"},
        )

    def test_single_day_empty_window_reconciles(self):
        day = date(2027, 12, 31)
        html = """
        <select id="filtreDepartementID"><option selected value="38">Isère</option></select>
        <select id="filtreNombreDeJoursID"><option selected value="1">1</option></select>
        <div id="cpContent_InfoJourSelection">0 compétition le vendredi 31 décembre 2027</div>
        """
        observation, links = parse_public_calendar(
            html,
            source_url=f"{BASE}/calendrier/?debut=2027-12-31&nbjours=1&departement=38",
            checked_at=NOW,
            requested=WindowRequest(day, day, "38"),
        )
        self.assertEqual(observation.status, "consistent_sample")
        self.assertEqual(observation.effective_start, day)
        self.assertEqual(observation.effective_end, day)
        self.assertEqual(observation.displayed_count, 0)
        self.assertEqual(links, {})

    def test_rejects_foreign_detail_links(self):
        html = calendar_html().replace(f'href="{PATH}"', f'href="https://elsewhere.invalid{PATH}"')
        with self.assertRaisesRegex(AdapterError, "invalid_source_url"):
            parse_calendar(html)

    def test_race_extracts_civil_dates_and_correlated_exact_rules(self):
        race, commune = parse_race(race_html("De U17 à U17", "Hommes tout âge", "Femmes tout âge"))
        self.assertEqual(race.start_date, date(2027, 1, 9))
        self.assertEqual(race.end_date, date(2027, 1, 10))
        self.assertEqual(race.discipline, "cyclocross")
        self.assertEqual(race.types, ())
        self.assertEqual(race.organizer, "Club Test")
        self.assertEqual(race.status, "unknown")
        self.assertEqual(race.department, "38")
        self.assertIsNone(commune)
        (scope,) = race.scopes
        self.assertEqual(scope.identity_status, "unverified")
        self.assertIsNone(scope.source_list_id)
        self.assertEqual(scope.eligibility_status, "confirmed")
        self.assertEqual(
            [(rule.category_codes, rule.restrictions.sex) for rule in scope.rules],
            [(("u17",), "men"), (("u17",), "women")],
        )
        self.assertTrue(
            all(rule.restrictions.engagers == ("Club", "Individuel") for rule in scope.rules)
        )

    def test_generic_category_and_unrecognized_age_do_not_become_rules(self):
        race, _ = parse_race(race_html("Access", "Hommes de 18 ans à 65 ans", "Femmes tout âge"))
        (scope,) = race.scopes
        self.assertEqual(scope.eligibility_status, "unknown")
        self.assertEqual(scope.rules, ())
        self.assertIn("Hommes de 18 ans à 65 ans", scope.raw_label)
        self.assertEqual(
            tuple(diagnostic.code for diagnostic in race.diagnostics), ("unknown_eligibility",)
        )

    def test_unparsed_content_in_the_criteria_does_not_confirm_rules(self):
        html = race_html("De U17 à U17", "Hommes tout âge").replace(
            '<div class="horizontal">', '<div class="horizontal"><div>Condition inconnue</div>'
        )
        race, _ = parse_race(html)
        self.assertEqual(race.scopes[0].eligibility_status, "unknown")
        self.assertEqual(race.scopes[0].rules, ())

    def test_type_and_commune_require_explicit_labels(self):
        race, commune = parse_race(
            race_html(
                "De U19 à U19",
                "Femmes tout âge",
                discipline="Route",
                extra=(("Type sportif", "CLM"), ("Commune", "Commune Test")),
            )
        )
        self.assertEqual(race.types, ("time_trial",))
        self.assertEqual(commune, "Commune Test")

    def test_explicit_department_conflict_is_rejected(self):
        with self.assertRaisesRegex(AdapterError, "department_mismatch"):
            parse_race(race_html(department="Drôme"))

    def test_race_code_conflict_is_rejected(self):
        with self.assertRaisesRegex(AdapterError, "conflicting_source_key"):
            parse_race(race_html(keys=("C4100091234", "2027")))

    def test_other_discipline_can_be_skipped(self):
        with self.assertRaisesRegex(AdapterError, "unsupported_discipline"):
            parse_race(race_html(discipline="BMX"))

    def test_mtb_discipline_does_not_guess_a_subtype(self):
        race, _ = parse_race(race_html(discipline="VTT"))
        self.assertEqual(race.discipline, "mtb")
        self.assertEqual(race.types, ())

    def test_source_season_is_independent_of_civil_year(self):
        race, _ = parse_race(race_html(day="vendredi 18 décembre 2026"))
        self.assertEqual(race.key.season, 2027)
        self.assertEqual(race.start_date, date(2026, 12, 18))

    def test_multi_day_range_requires_matching_duration(self):
        race, _ = parse_race(race_html(day="Du samedi 09 janvier 2027 au dimanche 10 janvier 2027"))
        self.assertEqual(race.end_date, date(2027, 1, 10))
        with self.assertRaisesRegex(AdapterError, "Date range contradicts race duration"):
            parse_race(race_html(day="Du samedi 09 janvier 2027 au lundi 11 janvier 2027"))

    def test_recovers_only_public_template_wrapper_omission(self):
        html = race_html().strip()
        (start, _div) = html.rsplit("</div>", 1)
        race, _ = parse_race("<span>" + start + "</span>")
        self.assertEqual(race.key, KEY)
        with self.assertRaisesRegex(AdapterError, "html_structure"):
            parse_race(html.replace("</h1>", "</span>"))
