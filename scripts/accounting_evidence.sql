SELECT name, docstatus, ROUND(grand_total, 2), ROUND(outstanding_amount, 2)
FROM `tabSales Invoice`
ORDER BY creation DESC
LIMIT 5;

SELECT voucher_no, COUNT(*), ROUND(SUM(debit), 2), ROUND(SUM(credit), 2)
FROM `tabGL Entry`
WHERE voucher_type = 'Sales Invoice'
GROUP BY voucher_no
ORDER BY MAX(creation) DESC
LIMIT 5;

SELECT name, docstatus, ROUND(paid_amount, 2), payment_type
FROM `tabPayment Entry`
ORDER BY creation DESC
LIMIT 5;
