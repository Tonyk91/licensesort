"""The canonical product catalog: the closed set every invoice line must map into.

Each entry carries the regex patterns the rules layer uses. Patterns run against
normalized text (lowercase, punctuation -> space, '+' kept), see rules.normalize.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    id: str
    vendor: str
    name: str
    patterns: tuple[str, ...]


_MS365 = r"(?:microsoft 365|m365|ms 365)"
_O365 = r"(?:office 365|o365|off365)"
_WINSRV = r"(?:windows server|winsvr|win svr|winsrv)"
_SQL = r"(?:sql server|sql svr|sql srv|sql)"

CATALOG: tuple[Product, ...] = (
    Product("M365-E3", "Microsoft", "Microsoft 365 E3", (rf"\b{_MS365} e3\b",)),
    Product("M365-E5", "Microsoft", "Microsoft 365 E5", (rf"\b{_MS365} e5\b",)),
    Product("M365-BP", "Microsoft", "Microsoft 365 Business Premium",
            (rf"\b{_MS365} (?:business|bus) (?:premium|prem)\b", rf"\b{_MS365} bp\b")),
    Product("O365-E1", "Microsoft", "Office 365 E1", (rf"\b{_O365} e1\b",)),
    Product("O365-E3", "Microsoft", "Office 365 E3", (rf"\b{_O365} e3\b",)),
    Product("PBI-PRO", "Microsoft", "Power BI Pro", (r"\b(?:power bi|pbi) pro\b",)),
    Product("VISIO-P2", "Microsoft", "Visio Plan 2", (r"\bvisio\b.*\b(?:plan 2|p2)\b",)),
    Product("PROJECT-P3", "Microsoft", "Project Plan 3", (r"\b(?:project|proj)\b.*\b(?:plan 3|p3)\b",)),
    Product("WINSRV-DC", "Microsoft", "Windows Server Datacenter",
            (rf"\b{_WINSRV}\b.*\b(?:datacenter|dc)\b",)),
    Product("WINSRV-STD", "Microsoft", "Windows Server Standard",
            (rf"\b{_WINSRV}\b.*\b(?:standard|std)\b",)),
    Product("SQL-STD", "Microsoft", "SQL Server Standard", (rf"\b{_SQL}\b.*\b(?:standard|std)\b",)),
    Product("SQL-ENT", "Microsoft", "SQL Server Enterprise", (rf"\b{_SQL}\b.*\b(?:enterprise|ent)\b",)),
    Product("ACROBAT-PRO", "Adobe", "Acrobat Pro", (r"\bacrobat\b.*\bpro\b",)),
    Product("ACROBAT-STD", "Adobe", "Acrobat Standard", (r"\bacrobat\b.*\b(?:standard|std)\b",)),
    Product("ADOBE-CC-ALL", "Adobe", "Creative Cloud All Apps",
            (r"\b(?:creative cloud|cc)\b.*\ball apps\b",)),
    Product("JIRA-STD", "Atlassian", "Jira Software Cloud Standard", (r"\bjira\b.*\b(?:standard|std)\b",)),
    Product("JIRA-PREM", "Atlassian", "Jira Software Cloud Premium", (r"\bjira\b.*\b(?:premium|prem)\b",)),
    Product("CONFLUENCE-STD", "Atlassian", "Confluence Cloud Standard",
            (r"\bconfluence\b.*\b(?:standard|std)\b",)),
    Product("SLACK-BPLUS", "Salesforce", "Slack Business+", (r"\bslack\b.*\bbusiness(?: ?\+| plus)",)),
    Product("ZOOM-PRO", "Zoom", "Zoom Workplace Pro", (r"\bzoom\b.*\bpro\b",)),
    Product("SFDC-SALES-ENT", "Salesforce", "Sales Cloud Enterprise",
            (r"\b(?:salesforce|sfdc)\b.*\bsales cloud\b.*\b(?:enterprise|ent)\b",)),
    Product("AUTOCAD", "Autodesk", "AutoCAD", (r"\bautocad\b(?! lt\b)",)),
    Product("AUTOCAD-LT", "Autodesk", "AutoCAD LT", (r"\bautocad lt\b",)),
    Product("TABLEAU-CREATOR", "Salesforce", "Tableau Creator", (r"\btableau\b.*\bcreator\b",)),
    Product("GITHUB-ENT", "GitHub", "GitHub Enterprise", (r"\b(?:github|gh)\b.*\b(?:enterprise|ent)\b",)),
    Product("INTELLIJ-ULT", "JetBrains", "IntelliJ IDEA Ultimate",
            (r"\bintellij\b.*\b(?:ultimate|ult)\b",)),
)

BY_ID = {p.id: p for p in CATALOG}
UNKNOWN = "UNKNOWN"
