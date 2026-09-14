from __future__ import annotations

from pathlib import Path
import json
import textwrap


ROOT = Path(__file__).resolve().parents[1]


REPOS = [
    {
        "name": "identity-core",
        "team": "Identity Platform",
        "business_unit": "Core Platform",
        "domain": "identity and access",
        "type": "service",
        "provides": ["authentication", "authorization", "token issuance", "service identity"],
        "depends_on": ["customer-profile", "notification-core"],
        "consumed_by": ["checkout-service", "merchant-service", "loan-orchestrator", "subscription-service"],
        "publishes": ["UserCreated", "IdentityVerified"],
        "subscribes": [],
        "data_owned": ["service credentials", "identity verification status"],
        "apis": ["POST /v1/auth/token", "GET /v1/users/{id}", "POST /v1/authorization/check"],
        "modules": {
            "services/token_service.py": "class TokenService:\n    def issue_token(self, subject, scopes):\n        return {'subject': subject, 'scopes': scopes, 'issuer': 'identity-core'}\n",
            "services/authorization_service.py": "class AuthorizationService:\n    def check(self, subject, action, resource):\n        return action in {'checkout:create', 'merchant:refund', 'loan:approve'}\n",
            "clients/customer_profile_client.py": "UPSTREAM_SERVICE = 'customer-profile'\nAPI_REFERENCE = 'GET /v1/customers/{id}'\n",
            "clients/notification_client.py": "UPSTREAM_SERVICE = 'notification-core'\nEVENT_REFERENCE = 'IdentityVerified'\n",
        },
        "note": "README still calls the service auth-core in a few places after a rename.",
    },
    {
        "name": "payment-core",
        "team": "Payments Platform",
        "business_unit": "Core Platform",
        "domain": "payments",
        "type": "service",
        "provides": ["payment authorization", "capture", "refund initiation", "payment status", "payment state transitions"],
        "depends_on": ["fraud-service", "identity-core", "ledger-core"],
        "consumed_by": ["checkout-service", "merchant-service", "subscription-service", "repayment-service"],
        "publishes": ["PaymentAuthorized", "PaymentCaptured", "PaymentRefundRequested", "PaymentFailed"],
        "subscribes": [],
        "data_owned": ["payment intents", "refund requests", "payment state"],
        "apis": ["POST /v1/payments/authorize", "POST /v1/payments/{id}/capture", "POST /v1/payments/{id}/refund", "GET /v1/payments/{id}"],
        "modules": {
            "payments/authorization/authorizer.py": "FRAUD_SERVICE = 'fraud-service'\nIDENTITY_SERVICE = 'identity-core'\nclass PaymentAuthorizer:\n    def authorize(self, amount, risk_decision):\n        if amount <= 0:\n            return 'declined'\n        return 'authorized' if risk_decision != 'block' else 'declined'\n",
            "payments/refunds/eligibility.py": "LEDGER_SERVICE = 'ledger-core'\nclass RefundEligibilityPolicy:\n    def decide(self, payment):\n        if payment.get('state') not in {'captured', 'settled'}:\n            return False, 'payment is not captured or settled'\n        if payment.get('chargeback_open'):\n            return False, 'chargeback already owns the dispute path'\n        if payment.get('refunded_amount', 0) >= payment.get('amount', 0):\n            return False, 'payment has already been fully refunded'\n        return True, 'eligible for merchant or support initiated refund'\n",
            "payments/refunds/workflow.py": "from payment_core.payments.refunds.eligibility import RefundEligibilityPolicy\nPUBLISHES_EVENT = 'PaymentRefundRequested'\nclass RefundWorkflow:\n    def request_refund(self, payment):\n        allowed, reason = RefundEligibilityPolicy().decide(payment)\n        return {'allowed': allowed, 'reason': reason, 'event': PUBLISHES_EVENT if allowed else None}\n",
            "payments/state/machine.py": "VALID_TRANSITIONS = {('authorized', 'captured'), ('captured', 'refund_requested'), ('captured', 'failed')}\n",
            "payments/risk/fraud_client.py": "UPSTREAM_SERVICE = 'fraud-service'\nAPI_REFERENCE = 'POST /v1/fraud/check'\n",
        },
        "note": "Refund eligibility lives here; ledger only records the accounting reversal.",
    },
    {
        "name": "customer-profile",
        "team": "Customer Platform",
        "business_unit": "Core Platform",
        "domain": "customer data",
        "type": "service",
        "provides": ["customer profile", "preferences", "contact details", "segmentation metadata"],
        "depends_on": [],
        "consumed_by": ["checkout-service", "subscription-service", "loan-orchestrator", "notification-core", "fraud-service", "risk-engine", "repayment-service"],
        "publishes": ["CustomerProfileUpdated"],
        "subscribes": ["UserCreated"],
        "data_owned": ["customer contact details", "preferences", "segments"],
        "apis": ["GET /v1/customers/{id}", "PATCH /v1/customers/{id}", "GET /v1/customers/{id}/preferences"],
        "modules": {
            "services/profile_service.py": "class ProfileService:\n    def get_profile(self, customer_id):\n        return {'id': customer_id, 'segment': 'standard', 'verified_income': False}\n",
            "events/handlers.py": "SUBSCRIBES_EVENT = 'UserCreated'\nPUBLISHES_EVENT = 'CustomerProfileUpdated'\n",
        },
        "note": "Owns contact data but not identity verification decisions.",
    },
    {
        "name": "notification-core",
        "team": "Notification Platform",
        "business_unit": "Core Platform",
        "domain": "notifications",
        "type": "service",
        "provides": ["email", "SMS", "push notifications", "notification templates", "delivery tracking"],
        "depends_on": ["customer-profile"],
        "consumed_by": ["identity-core", "subscription-service", "loan-orchestrator", "repayment-service"],
        "publishes": ["NotificationSent", "NotificationFailed"],
        "subscribes": ["PaymentFailed", "PaymentRefundRequested", "LoanApproved", "LoanRejected"],
        "data_owned": ["delivery attempts", "template versions"],
        "apis": ["POST /v1/notifications/send", "GET /v1/notifications/{id}"],
        "modules": {
            "services/template_router.py": "PAYMENT_FAILURE_TEMPLATE = 'payment-failed-email'\nREFUND_TEMPLATE = 'refund-requested-email'\n",
            "events/payment_handlers.py": "SUBSCRIBES_EVENTS = ['PaymentFailed', 'PaymentRefundRequested']\nCUSTOMER_SERVICE = 'customer-profile'\n",
        },
        "note": "Contains payment failure wording but does not detect failures.",
    },
    {
        "name": "fraud-service",
        "team": "Payments Platform",
        "business_unit": "Core Platform",
        "domain": "fraud risk",
        "type": "service",
        "provides": ["fraud scoring", "transaction risk checks", "fraud decisions"],
        "depends_on": ["customer-profile", "identity-core"],
        "consumed_by": ["payment-core", "checkout-service"],
        "publishes": ["FraudCheckCompleted"],
        "subscribes": [],
        "data_owned": ["fraud scores", "risk signals"],
        "apis": ["POST /v1/fraud/check"],
        "modules": {
            "services/risk_score.py": "class FraudDecision:\n    def decide(self, amount, customer_segment):\n        score = min(99, amount // 100 + (25 if customer_segment == 'new' else 0))\n        return {'score': score, 'decision': 'block' if score >= 80 else 'review' if score >= 50 else 'allow'}\n",
            "clients/identity_client.py": "UPSTREAM_SERVICE = 'identity-core'\n",
            "clients/customer_profile_client.py": "UPSTREAM_SERVICE = 'customer-profile'\n",
        },
        "note": "Checkout sometimes calls this directly for pre-screening, which is intentionally duplicated.",
    },
    {
        "name": "ledger-core",
        "team": "Finance Platform",
        "business_unit": "Core Platform",
        "domain": "ledger and accounting",
        "type": "service",
        "provides": ["accounting entries", "payment ledger", "refund reversals", "reconciliation primitives"],
        "depends_on": [],
        "consumed_by": ["payment-core", "repayment-service", "merchant-service"],
        "publishes": ["LedgerEntryPosted", "LedgerReversalPosted"],
        "subscribes": ["PaymentAuthorized", "PaymentCaptured", "PaymentRefundRequested"],
        "data_owned": ["journal entries", "ledger transactions", "reversals"],
        "apis": ["POST /v1/ledger/entries", "POST /v1/ledger/reversals", "GET /v1/ledger/transactions/{id}"],
        "modules": {
            "services/reversal_service.py": "class ReversalService:\n    def create_reversal(self, payment_id, amount):\n        return {'payment_id': payment_id, 'amount': amount, 'type': 'refund_reversal'}\n",
            "events/payment_event_recorder.py": "SUBSCRIBES_EVENTS = ['PaymentCaptured', 'PaymentRefundRequested']\n",
        },
        "note": "Uses refund/reversal language but does not decide refund eligibility.",
    },
    {
        "name": "checkout-service",
        "team": "Checkout",
        "business_unit": "Retail Business",
        "domain": "checkout orchestration",
        "type": "service",
        "provides": ["shopping cart checkout", "order creation", "payment orchestration", "promotion validation"],
        "depends_on": ["identity-core", "customer-profile", "payment-core", "fraud-service"],
        "consumed_by": [],
        "publishes": ["CheckoutCompleted", "CheckoutFailed"],
        "subscribes": [],
        "data_owned": ["checkout sessions", "orders"],
        "apis": ["POST /v1/checkout", "POST /v1/checkout/{id}/retry"],
        "modules": {
            "services/checkout_orchestrator.py": "IDENTITY_SERVICE = 'identity-core'\nCUSTOMER_SERVICE = 'customer-profile'\nPAYMENT_SERVICE = 'payment-core'\nFRAUD_SERVICE = 'fraud-service'\nclass CheckoutOrchestrator:\n    def submit(self, cart):\n        return {'step': 'authorize payment through payment-core', 'owns_decision': False}\n",
            "clients/payment_client.py": "UPSTREAM_SERVICE = 'payment-core'\nAPI_REFERENCE = 'POST /v1/payments/authorize'\n",
        },
        "note": "Orchestrates card acceptance but payment-core owns the final payment decision.",
    },
    {
        "name": "merchant-service",
        "team": "Merchant Operations",
        "business_unit": "Retail Business",
        "domain": "merchant operations",
        "type": "service",
        "provides": ["merchant transaction lookup", "merchant refund initiation", "settlement views"],
        "depends_on": ["payment-core", "ledger-core", "identity-core"],
        "consumed_by": [],
        "publishes": ["MerchantRefundRequested"],
        "subscribes": ["PaymentRefundRequested"],
        "data_owned": ["merchant cases", "refund initiation audit"],
        "apis": ["POST /v1/merchants/{id}/refunds", "GET /v1/merchants/{id}/transactions"],
        "modules": {
            "services/refund_case_service.py": "PAYMENT_SERVICE = 'payment-core'\nLEDGER_SERVICE = 'ledger-core'\nclass RefundCaseService:\n    def open_case(self, payment_id):\n        return {'payment_id': payment_id, 'delegates_eligibility_to': PAYMENT_SERVICE}\n",
            "clients/payment_client.py": "UPSTREAM_SERVICE = 'payment-core'\nAPI_REFERENCE = 'POST /v1/payments/{id}/refund'\n",
        },
        "note": "Many docs say merchant refunds, but it initiates rather than decides eligibility.",
    },
    {
        "name": "subscription-service",
        "team": "Subscription Commerce",
        "business_unit": "Retail Business",
        "domain": "recurring commerce",
        "type": "service",
        "provides": ["recurring billing", "subscription lifecycle", "scheduled charges", "failed-payment retries"],
        "depends_on": ["payment-core", "customer-profile", "notification-core"],
        "consumed_by": [],
        "publishes": ["SubscriptionSuspended", "SubscriptionRenewed"],
        "subscribes": ["PaymentFailed"],
        "data_owned": ["subscriptions", "billing schedules", "retry state"],
        "apis": ["POST /v1/subscriptions", "POST /v1/subscriptions/{id}/retry"],
        "modules": {
            "services/retry_policy.py": "MAX_RETRIES = 3\nGRACE_PERIOD_DAYS = 7\nclass BillingRetryPolicy:\n    def next_action(self, failures):\n        return 'suspend' if failures >= MAX_RETRIES else 'retry'\n",
            "clients/payment_client.py": "UPSTREAM_SERVICE = 'payment-core'\nAPI_REFERENCE = 'POST /v1/payments/authorize'\n",
            "events/payment_failed_handler.py": "SUBSCRIBES_EVENT = 'PaymentFailed'\nNOTIFICATION_SERVICE = 'notification-core'\n",
        },
        "note": "Retry behavior here is subscription billing retry, not payment authorization retry.",
    },
    {
        "name": "loan-orchestrator",
        "team": "Loan Orchestration",
        "business_unit": "Lending Business",
        "domain": "loan workflows",
        "type": "service",
        "provides": ["loan application workflow", "customer verification", "risk evaluation orchestration", "loan state transitions"],
        "depends_on": ["identity-core", "customer-profile", "risk-engine", "notification-core"],
        "consumed_by": [],
        "publishes": ["LoanApproved", "LoanRejected"],
        "subscribes": ["IdentityVerified"],
        "data_owned": ["loan applications", "loan workflow state"],
        "apis": ["POST /v1/loans/apply", "GET /v1/loans/{id}", "POST /v1/loans/{id}/approve"],
        "modules": {
            "services/application_workflow.py": "IDENTITY_SERVICE = 'identity-core'\nCUSTOMER_SERVICE = 'customer-profile'\nRISK_SERVICE = 'risk-engine'\nclass LoanWorkflow:\n    def decide(self, risk_result):\n        return 'approved' if risk_result['eligible'] else 'rejected'\n",
            "clients/risk_client.py": "UPSTREAM_SERVICE = 'risk-engine'\nAPI_REFERENCE = 'POST /v1/risk/loan-score'\n",
        },
        "note": "Owns workflow state; risk-engine owns eligibility scoring.",
    },
    {
        "name": "risk-engine",
        "team": "Risk Engine",
        "business_unit": "Lending Business",
        "domain": "credit decisioning",
        "type": "service",
        "provides": ["credit scoring", "loan eligibility rules", "decisioning inputs"],
        "depends_on": ["customer-profile", "identity-core"],
        "consumed_by": ["loan-orchestrator"],
        "publishes": ["RiskDecisionCalculated"],
        "subscribes": [],
        "data_owned": ["risk decisions", "score explanations"],
        "apis": ["POST /v1/risk/loan-score"],
        "modules": {
            "services/eligibility_rules.py": "class LoanEligibilityRules:\n    def evaluate(self, profile, requested_amount):\n        if not profile.get('verified_income'):\n            return {'eligible': False, 'reason': 'income is not verified'}\n        if requested_amount > 50000:\n            return {'eligible': False, 'reason': 'requested amount exceeds unsecured limit'}\n        return {'eligible': True, 'reason': 'within policy'}\n",
            "clients/customer_profile_client.py": "UPSTREAM_SERVICE = 'customer-profile'\n",
        },
        "note": "Best answer for loan eligibility questions even though loan-orchestrator exposes the public loan API.",
    },
    {
        "name": "repayment-service",
        "team": "Repayment",
        "business_unit": "Lending Business",
        "domain": "loan repayment",
        "type": "service",
        "provides": ["repayment schedules", "payment collection", "failed repayment handling", "ledger integration"],
        "depends_on": ["payment-core", "ledger-core", "customer-profile", "notification-core"],
        "consumed_by": [],
        "publishes": ["RepaymentCollected", "RepaymentFailed"],
        "subscribes": ["PaymentFailed"],
        "data_owned": ["repayment schedules", "collection attempts"],
        "apis": ["POST /v1/repayments/collect", "GET /v1/repayments/{id}/schedule"],
        "modules": {
            "services/collection_service.py": "PAYMENT_SERVICE = 'payment-core'\nLEDGER_SERVICE = 'ledger-core'\nclass CollectionService:\n    def collect(self, installment):\n        return {'delegates_payment_to': PAYMENT_SERVICE, 'records_to': LEDGER_SERVICE}\n",
            "events/payment_failed_handler.py": "SUBSCRIBES_EVENT = 'PaymentFailed'\n",
        },
        "note": "Overlaps with payment failure terms but owns repayment handling only.",
    },
]


INFRA_REPOS = [
    {
        "name": "platform-infra",
        "team": "Developer Platform / Infrastructure",
        "business_unit": "Infrastructure / Developer Platform",
        "domain": "shared infrastructure",
        "type": "infrastructure",
        "provides": ["Terraform networking", "managed databases", "queues and topics", "IAM roles"],
        "depends_on": [],
        "consumed_by": ["identity-core", "payment-core", "checkout-service", "loan-orchestrator", "subscription-service"],
        "publishes": [],
        "subscribes": [],
        "data_owned": ["infrastructure state"],
        "apis": [],
    },
    {
        "name": "deployment-platform",
        "team": "Developer Platform",
        "business_unit": "Infrastructure / Developer Platform",
        "domain": "deployments",
        "type": "deployment",
        "provides": ["Helm charts", "deployment configuration", "environment configuration", "rollout policies"],
        "depends_on": ["platform-infra"],
        "consumed_by": ["identity-core", "payment-core", "checkout-service", "merchant-service", "subscription-service", "loan-orchestrator", "repayment-service"],
        "publishes": [],
        "subscribes": [],
        "data_owned": ["deployment templates"],
        "apis": [],
    },
    {
        "name": "observability-platform",
        "team": "Developer Platform",
        "business_unit": "Infrastructure / Developer Platform",
        "domain": "observability",
        "type": "observability",
        "provides": ["dashboards", "alerts", "logging configuration", "tracing", "SLO definitions"],
        "depends_on": ["deployment-platform"],
        "consumed_by": ["payment-core", "checkout-service", "subscription-service", "loan-orchestrator", "repayment-service"],
        "publishes": [],
        "subscribes": ["PaymentFailed", "PaymentRefundRequested", "LoanRejected"],
        "data_owned": ["dashboards", "alert definitions", "trace sampling policies"],
        "apis": [],
    },
]


def slug_module(name: str) -> str:
    return name.replace("-", "_")


def yaml_list(values: list[str], indent: int = 2) -> str:
    if not values:
        return " []"
    pad = " " * indent
    return "\n" + "\n".join(f"{pad}- {value}" for value in values)


def service_yaml(repo: dict) -> str:
    fields = [
        ("name", repo["name"]),
        ("team", repo["team"]),
        ("business_unit", repo["business_unit"]),
        ("domain", repo["domain"]),
        ("type", repo["type"]),
    ]
    out = [f"{key}: {value}" for key, value in fields]
    for key in ["provides", "apis", "depends_on", "consumed_by", "publishes", "subscribes", "data_owned"]:
        out.append(f"{key}:{yaml_list(repo.get(key, []))}")
    out.append("criticality: high" if repo["name"] in {"payment-core", "identity-core", "ledger-core"} else "criticality: medium")
    return "\n".join(out) + "\n"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def write_service_repo(repo: dict) -> None:
    base = ROOT / "enterprise-repos" / repo["name"]
    mod = slug_module(repo["name"])
    write(base / "SERVICE.yaml", service_yaml(repo))
    write(base / "OWNERS", f"team: {repo['team']}\nslack: #{repo['team'].lower().replace(' ', '-')}\nescalation: atlas-{repo['name']}@example.com\n")
    write(base / "README.md", f"""
    # {repo['name']}

    {repo['name']} is owned by {repo['team']} in {repo['business_unit']}. It provides {", ".join(repo['provides'])}.

    Important caveat: {repo.get('note', 'Some dependencies are documented in code and deployment files rather than only in SERVICE.yaml.')}

    ## Runtime Dependencies
    {chr(10).join(f"- {dep}" for dep in repo.get('depends_on', [])) or "- none"}

    ## Public APIs
    {chr(10).join(f"- `{api}`" for api in repo.get('apis', [])) or "- internal only"}
    """)
    write(base / "ARCHITECTURE.md", f"""
    # Architecture

    Domain: {repo['domain']}.

    This repository is part of Atlas Commerce Group's {repo['business_unit']} area. It exposes capabilities around {", ".join(repo['provides'])}.

    Dependencies are called through small clients under `src/{mod}/clients` when present. Event names are intentionally present in code and docs so topology extraction can discover them.

    Publishes: {", ".join(repo.get('publishes', [])) or "none"}.
    Subscribes: {", ".join(repo.get('subscribes', [])) or "none"}.
    """)
    write(base / "API.md", "\n".join([f"# API\n"] + [f"- `{api}`" for api in repo.get("apis", [])]) + "\n")
    write(base / "docs/RUNBOOK.md", f"""
    # Runbook

    Start investigations by checking owned data: {", ".join(repo['data_owned'])}.
    For dependency incidents, inspect {", ".join(repo.get('depends_on', [])) or "local logs"} before escalating.
    """)
    write(base / "docs/adr/0001-service-boundaries.md", f"""
    # ADR 0001: Service Boundary

    {repo['name']} owns {repo['domain']} concerns. Similar terms may appear in neighboring repositories, but ownership follows the data and decisions listed in SERVICE.yaml.
    """)
    write(base / "pyproject.toml", f"""
    [project]
    name = "{repo['name']}"
    version = "0.1.0"
    dependencies = ["fastapi"]
    """)
    write(base / f"src/{mod}/__init__.py", "")
    write(base / f"src/{mod}/api/routes.py", f"""
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/health")
    def health():
        return {{"service": "{repo['name']}", "status": "ok"}}
    """)
    write(base / f"src/{mod}/domain/models.py", f"""
    from dataclasses import dataclass

    @dataclass
    class ServiceRecord:
        id: str
        owner: str = "{repo['team']}"
    """)
    write(base / f"src/{mod}/config/settings.py", f"""
    SERVICE_NAME = "{repo['name']}"
    DEPENDS_ON = {repo.get('depends_on', [])!r}
    PUBLISHES = {repo.get('publishes', [])!r}
    SUBSCRIBES = {repo.get('subscribes', [])!r}
    """)
    write(base / f"src/{mod}/events/events.py", f"""
    PUBLISHES = {repo.get('publishes', [])!r}
    SUBSCRIBES = {repo.get('subscribes', [])!r}
    """)
    for rel, content in repo.get("modules", {}).items():
        write(base / f"src/{mod}" / rel, content)
    write(base / "tests/test_metadata.py", f"""
    from pathlib import Path

    def test_service_metadata_names_repo():
        assert "name: {repo['name']}" in Path("SERVICE.yaml").read_text()
    """)


def write_infra_repo(repo: dict) -> None:
    base = ROOT / "enterprise-repos" / repo["name"]
    write(base / "SERVICE.yaml", service_yaml(repo))
    write(base / "OWNERS", f"team: {repo['team']}\nslack: #developer-platform\n")
    write(base / "README.md", f"# {repo['name']}\n\nOwns {', '.join(repo['provides'])} for Atlas Commerce Group.\n")
    write(base / "ARCHITECTURE.md", f"# Architecture\n\n{repo['name']} supports {', '.join(repo.get('consumed_by', []))}.\n")
    write(base / "API.md", "# API\n\nInfrastructure repository; no public business API.\n")
    if repo["name"] == "platform-infra":
        write(base / "terraform/networking/main.tf", 'resource "aws_vpc" "atlas" { cidr_block = "10.42.0.0/16" }\n')
        write(base / "terraform/databases/payment_core.tf", 'resource "aws_db_instance" "payment_core" { engine = "postgres" }\n')
        write(base / "terraform/messaging/payment_events.tf", 'resource "aws_sns_topic" "payment_failed" { name = "PaymentFailed" }\nresource "aws_sns_topic" "payment_refund_requested" { name = "PaymentRefundRequested" }\n')
        write(base / "terraform/iam/service_roles.tf", 'locals { services = ["payment-core", "checkout-service", "loan-orchestrator"] }\n')
    elif repo["name"] == "deployment-platform":
        write(base / "helm/payment-core/values-prod.yaml", "service: payment-core\nhttp:\n  timeout_ms: 2500\n  retries: 2\n")
        write(base / "helm/checkout-service/values-prod.yaml", "service: checkout-service\nupstreams:\n  payment-core:\n    timeout_ms: 1800\n")
        write(base / "kubernetes/templates/deployment.yaml", "kind: Deployment\nmetadata:\n  labels:\n    atlas/service: '{{ .Values.service }}'\n")
    else:
        write(base / "alerts/payment-timeouts.yaml", "groups:\n- name: payment-timeouts\n  rules:\n  - alert: PaymentCoreTimeoutsHigh\n    expr: rate(http_client_timeout_total{service=\"payment-core\"}[5m]) > 0.05\n")
        write(base / "dashboards/payment-core.json", json.dumps({"title": "payment-core health", "panels": ["latency", "timeouts", "PaymentFailed events"]}, indent=2))
        write(base / "otel/service-labels.yaml", "services:\n  payment-core:\n    traces: sampled\n  checkout-service:\n    traces: sampled\n")


def write_root_files() -> None:
    write(ROOT / "README.md", """
    # Enterprise Repo Intelligence

    A working research prototype for routing natural-language engineering questions to the smallest relevant slice of a simulated enterprise software ecosystem.

    ## Quick start

    ```bash
    python -m app.seed
    python -m evaluation.evaluate_routing
    uvicorn app.api.main:app --reload
    ```

    Docker Compose provides PostgreSQL for later experiments, while the current deterministic prototype stores its registry in `data/registry.json` so it can run without external services.
    """)
    write(ROOT / "ENTERPRISE_ARCHITECTURE.md", """
    # Atlas Commerce Group Enterprise Architecture

    Atlas Commerce Group has core platform teams for identity, payments, customer data, notifications, and finance. Retail business services compose checkout, merchant operations, and subscription commerce on top of those platforms. Lending business services orchestrate loans, risk decisions, and repayment collection.

    The most important payment flow is checkout-service -> fraud-service -> payment-core -> ledger-core. Refunds usually begin in merchant-service, but payment-core decides eligibility and ledger-core records the accounting reversal.

    Loan decisions flow through loan-orchestrator -> risk-engine -> customer-profile. Operational questions about timeouts, deployments, or alerts often route to deployment-platform or observability-platform rather than application code.
    """)
    write(ROOT / "pyproject.toml", """
    [project]
    name = "enterprise-repo-intelligence"
    version = "0.1.0"
    requires-python = ">=3.11"
    dependencies = [
      "fastapi>=0.110",
      "uvicorn>=0.27",
      "pydantic>=2",
      "sqlalchemy>=2",
      "psycopg[binary]>=3",
      "pgvector>=0.2",
      "pyyaml>=6",
    ]

    [tool.pytest.ini_options]
    pythonpath = ["."]
    testpaths = ["tests"]
    """)
    write(ROOT / "docker-compose.yml", """
    services:
      postgres:
        image: pgvector/pgvector:pg16
        environment:
          POSTGRES_DB: repo_intelligence
          POSTGRES_USER: atlas
          POSTGRES_PASSWORD: atlas
        ports:
          - "5432:5432"
    """)


def main() -> None:
    write_root_files()
    for repo in REPOS:
        write_service_repo(repo)
    for repo in INFRA_REPOS:
        write_infra_repo(repo)
    print(f"Scaffolded {len(REPOS) + len(INFRA_REPOS)} enterprise repositories")


if __name__ == "__main__":
    main()
