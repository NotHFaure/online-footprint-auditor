"""A curated subset of known data-broker / people-search sites.

Sourced from github.com/yaelwrites/Big-Ass-Data-Broker-Opt-Out-List (fetched
2026-07-30), plus the three named directly in the PRD/tasks.md (Spokeo,
WhitePages, BeenVerified). This is a starting subset, not the full list —
expanding coverage is a content task, not an architecture one.

`supports_automated_optout` is set to False for every entry here deliberately:
determining which of these sites genuinely expose a scriptable opt-out flow is
real per-site research belonging to tasks.md Phase 4, not fabricated here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrokerEntry:
    name: str
    url: str
    domain: str
    supports_automated_optout: bool


BROKERS: list[BrokerEntry] = [
    BrokerEntry("Spokeo", "https://www.spokeo.com/search", "spokeo.com", False),
    BrokerEntry("WhitePages", "https://www.whitepages.com/", "whitepages.com", False),
    BrokerEntry(
        "BeenVerified",
        "https://www.beenverified.com/app/optout/search",
        "beenverified.com",
        False,
    ),
    BrokerEntry("Intelius", "https://www.intelius.com/", "intelius.com", False),
    BrokerEntry("MyLife", "https://www.mylife.com", "mylife.com", False),
    BrokerEntry("Nuwber", "https://nuwber.com/", "nuwber.com", False),
    BrokerEntry("Radaris", "https://radaris.com/", "radaris.com", False),
    BrokerEntry(
        "SmartBackgroundChecks",
        "https://www.smartbackgroundchecks.com/",
        "smartbackgroundchecks.com",
        False,
    ),
    BrokerEntry("That's Them", "https://thatsthem.com/", "thatsthem.com", False),
    BrokerEntry(
        "AdvancedBackgroundChecks",
        "https://www.advancedbackgroundchecks.com",
        "advancedbackgroundchecks.com",
        False,
    ),
    BrokerEntry(
        "FamilyTreeNow", "https://www.familytreenow.com/optout", "familytreenow.com", False
    ),
    BrokerEntry(
        "FastPeopleSearch", "https://www.fastpeoplesearch.com/", "fastpeoplesearch.com", False
    ),
    BrokerEntry("USPhoneBook", "https://www.usphonebook.com/opt-out/", "usphonebook.com", False),
    BrokerEntry("CheckPeople", "https://checkpeople.com/privacy-rights", "checkpeople.com", False),
]
