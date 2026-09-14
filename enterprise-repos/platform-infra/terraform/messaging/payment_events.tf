resource "aws_sns_topic" "payment_failed" { name = "PaymentFailed" }
resource "aws_sns_topic" "payment_refund_requested" { name = "PaymentRefundRequested" }
