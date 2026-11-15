# Candidate Open Arabic Font Families

This is a discovery list for a pilot corpus, not a statement that the files have already been downloaded or validated. For every exact font version, inspect its repository and license file, record the version and SHA-256, and verify Arabic coverage before inclusion.

| Candidate family | Design coverage | Primary source |
|---|---|---|
| Noto Naskh Arabic | Naskh | https://github.com/google/fonts |
| Amiri | Naskh / book typography | https://github.com/alif-type/amiri |
| Scheherazade New | Naskh / extended Arabic-script coverage | https://github.com/silnrsi/font-scheherazade |
| Lateef | Arabic-script text | https://github.com/silnrsi/font-lateef |
| Cairo | Sans / display | https://github.com/google/fonts |
| Tajawal | Sans | https://github.com/google/fonts |
| IBM Plex Sans Arabic | Sans | https://github.com/IBM/plex |
| Mada | Sans | https://github.com/google/fonts |
| Reem Kufi | Kufi / display | https://github.com/google/fonts |

## Inclusion checklist

- [ ] Exact source repository and release/tag recorded.
- [ ] License file for the exact release inspected; redistribution and derivative-work terms understood.
- [ ] Font binary SHA-256 recorded.
- [ ] Family/style/weight metadata extracted.
- [ ] Arabic Unicode coverage checked from cmap and actual shaping tests.
- [ ] Font family assigned to exactly one split.
- [ ] No duplicate family/style file under a different filename.

Do not assume every family covers the same Arabic-script languages. Add a family to the manifest only after verification.
