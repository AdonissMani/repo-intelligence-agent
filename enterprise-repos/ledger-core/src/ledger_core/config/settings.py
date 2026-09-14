SERVICE_NAME = "ledger-core"
DEPENDS_ON = []
PUBLISHES = ['LedgerEntryPosted', 'LedgerReversalPosted']
SUBSCRIBES = ['PaymentAuthorized', 'PaymentCaptured', 'PaymentRefundRequested']
