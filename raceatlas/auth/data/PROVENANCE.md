# Common-password corpus provenance

Unmodified `common-passwords.txt.gz`, Django **6.0** tag:
https://raw.githubusercontent.com/django/django/6.0/django/contrib/auth/common-passwords.txt.gz
SHA256 `3c1baed62596de36860824eb3f436d5932d37ca8b06e59df78f5a44ec175afe4`, 80,228 bytes compressed /162,384 decoded, 19,640 distinct entries (48 length>=15; longest33). Cache downloaded13November2026; copied after explicit C attribution. No Django dependency installed.

Distributor license retained in DJANGO-LICENSE.txt, read13November2026:
https://raw.githubusercontent.com/django/django/6.0/LICENSE
Django source credits Royce Williams:
https://github.com/django/django/blob/6.0/django/contrib/auth/password_validation.py
https://gist.github.com/roycewilliams/226886fd01572964e1431ac8afc999ce

Reliance on Django's BSD3 distribution/provenance, not a comprehensive legal audit of upstream password compilations. Dataset is historic, not an up-to-date compromised-password service or exhaustive protection. RaceAtlas compares the WHOLE EXACT string, case-sensitive, without trimming/normalization or substring checks. Login verification is unchanged; only new-secret setters use this policy. Source entries were already lowercased upstream, so case/space variants can remain admissible. Original bytes to Argon2 remain exact.
