"""Classify a job listing for a graduate network-engineering search.

Pure standard library. Works on plain text (title + description).
"""
import re
from dataclasses import dataclass, field, asdict

GRAD_TERMS = [
    r"graduate", r"university grad", r"new grad", r"early careers?",
    r"early talent", r"campus", r"class of \d{4}", r"graduate scheme",
    r"graduate programme", r"graduate program",
]
PLACEMENT_TERMS = [
    r"placement", r"industrial placement", r"intern(ship)?",
    r"sandwich year", r"year in industry", r"co-?op",
]
JUNIOR_TERMS = [r"entry[- ]level", r"junior", r"associate", r"trainee",
                r"apprentice(ship)?", r"no experience"]
SENIOR_TERMS = [r"senior", r"\blead\b", r"principal", r"staff engineer",
                r"head of", r"manager", r"architect", r"director",
                r"\d\+?\s*years'? (of )?experience"]

NETWORK_TERMS = [
    r"network", r"noc\b", r"routing", r"switching", r"cisco", r"ccna", r"ccnp",
    r"juniper", r"arista", r"firewall", r"sd-?wan", r"bgp", r"ospf", r"tcp/?ip",
    r"infrastructure", r"telecom", r"wireless", r"lan\b", r"wan\b",
    r"site reliability", r"cloud networking", r"connectivity",
]

CLEARANCE_RE = re.compile(
    r"(security clearance|sc clearance|dv clearance|\bBPSS\b|\bCTC\b|"
    r"eligib\w+ (for|to obtain) (sc|dv|security)|uk national|british (citizen|national)|"
    r"must be (a )?(uk|us|u\.s\.) (citizen|national)|us citizenship|"
    r"export control|itar|polygraph)", re.I)

VISA_POS_RE = re.compile(r"(visa sponsorship (is )?(available|provided|offered)|"
                         r"we (can )?sponsor|will sponsor)", re.I)
VISA_NEG_RE = re.compile(r"(no (visa )?sponsorship|(unable|not able) to sponsor|"
                         r"without (the need for )?sponsorship|right to work (in the )?(uk|us)\b)", re.I)

YEAR_RE = re.compile(r"\b(202[6-9]|2030)\b")


def _any(patterns, text):
    return any(re.search(p, text, re.I) for p in patterns)


def _work_pattern(text):
    t = text.lower()
    if re.search(r"\bhybrid\b|\d\s*-\s*\d\s*days (per|a) week|\d days (per|a) week (in|on)", t):
        return "hybrid"
    if re.search(r"\bfully remote\b|\bremote[- ](first|only)\b|\b100% remote\b|work from home", t):
        return "remote"
    if re.search(r"\bremote\b", t):
        return "remote/possible"
    if re.search(r"\bon[- ]?site\b|office[- ]based", t):
        return "on-site"
    return "unknown"


@dataclass
class Tagged:
    title: str
    kind: str                 # graduate | placement | junior | experienced | other
    network_relevant: bool
    years: list = field(default_factory=list)
    work_pattern: str = "unknown"
    clearance_or_nationality: bool = False
    visa: str = "unknown"     # sponsors | no | unknown
    fit: str = ""             # match | check | too_early | too_late | not_relevant
    fit_reason: str = ""

    def as_dict(self):
        return asdict(self)


def classify(title: str, description: str = "", grad_year: int = 2028) -> Tagged:
    text = f"{title}\n{description}"
    title_l = title.lower()

    is_grad = _any(GRAD_TERMS, text)
    is_place = _any(PLACEMENT_TERMS, text)
    is_junior = _any(JUNIOR_TERMS, text)
    is_senior = _any(SENIOR_TERMS, title_l) or (
        not is_grad and _any(SENIOR_TERMS, text))

    # A "graduate" signal in the title beats a senior-looking word elsewhere.
    if is_grad and _any(GRAD_TERMS, title_l):
        kind = "graduate"
    elif is_place and _any(PLACEMENT_TERMS, title_l):
        kind = "placement"
    elif is_senior:
        kind = "experienced"
    elif is_grad:
        kind = "graduate"
    elif is_place:
        kind = "placement"
    elif is_junior:
        kind = "junior"
    else:
        kind = "other"

    years = sorted({int(y) for y in YEAR_RE.findall(text)})
    t = Tagged(
        title=title,
        kind=kind,
        network_relevant=_any(NETWORK_TERMS, text),
        years=years,
        work_pattern=_work_pattern(text),
        clearance_or_nationality=bool(CLEARANCE_RE.search(text)),
        visa=("sponsors" if VISA_POS_RE.search(text)
              else "no" if VISA_NEG_RE.search(text) else "unknown"),
    )

    # ---- fit for the user's graduation year ----
    if not t.network_relevant:
        t.fit, t.fit_reason = "not_relevant", "no networking keywords"
    elif kind == "experienced":
        t.fit, t.fit_reason = "not_relevant", "looks like an experienced role"
    elif kind == "graduate":
        if grad_year in years:
            t.fit, t.fit_reason = "match", f"mentions {grad_year}"
        elif years and max(years) < grad_year:
            t.fit, t.fit_reason = "too_early", f"aimed at class of {max(years)}"
        elif years and min(years) > grad_year:
            t.fit, t.fit_reason = "too_late", f"aimed at class of {min(years)}"
        else:
            t.fit, t.fit_reason = "check", "graduate role, no year stated"
    elif kind == "placement":
        want = grad_year - 1  # placement / internship the year before finishing
        if want in years:
            t.fit, t.fit_reason = "match", f"placement in {want}, the year before you graduate"
        elif years and max(years) < want:
            t.fit, t.fit_reason = "too_early", f"placement dated {max(years)}"
        else:
            t.fit, t.fit_reason = "check", "placement/internship, check dates"
    elif kind == "junior":
        t.fit, t.fit_reason = "check", "entry-level, not tied to a graduation date"
    else:
        t.fit, t.fit_reason = "not_relevant", "no graduate/entry-level signal"
    return t
