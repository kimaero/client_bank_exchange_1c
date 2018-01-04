from typing import List, Optional

from django.db import models
from client_bank_exchange_1c import (
    Statement, Header, Balance, Document, Payer, Payment, Receipt, Receiver, Special,
    Tax,
)


class DjangoStatement(models.Model):
    """
    Базовая абстрактная Django-модель для сохранения выписки из формата 1CClientBankExchange
    """

    class Meta:
        abstract = True

    format_version = models.TextField(null=True, blank=True)
    encoding = models.TextField(null=True, blank=True)
    sender = models.TextField(null=True, blank=True)
    receiver = models.TextField(null=True, blank=True)
    creation_date = models.DateField(null=True, blank=True)
    creation_time = models.TimeField(null=True, blank=True)
    filter_date_since = models.DateField(null=True, blank=True)
    filter_date_till = models.DateField(null=True, blank=True)
    balance_date_since = models.DateField(null=True, blank=True)
    balance_date_till = models.DateField(null=True, blank=True)
    balance_account_number = models.CharField(max_length=20, null=True, blank=True)
    balance_initial_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    balance_total_income = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    balance_total_expense = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    balance_final_balance = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    @classmethod
    def from_statement(cls, statement: Statement):
        return cls(
            format_version=statement.header.format_version,
            encoding=statement.header.encoding,
            sender=statement.header.sender,
            receiver=statement.header.receiver,
            creation_date=statement.header.creation_date,
            creation_time=statement.header.creation_time,
            filter_date_since=statement.header.filter_date_since,
            filter_date_till=statement.header.filter_date_till,
            balance_date_since=statement.balance.date_since,
            balance_date_till=statement.balance.date_till,
            balance_account_number=statement.balance.account_number,
            balance_initial_balance=statement.balance.initial_balance,
            balance_total_income=statement.balance.total_income,
            balance_total_expense=statement.balance.total_expense,
            balance_final_balance=statement.balance.final_balance
        )

    # noinspection PyTypeChecker
    def to_statement(self, documents: Optional[List[Document]]=None):
        return Statement(
            header=Header(
                format_version=self.format_version,
                encoding=self.encoding,
                sender=self.sender,
                receiver=self.receiver,
                creation_date=self.creation_date,
                creation_time=self.creation_time,
                filter_date_since=self.filter_date_since,
                filter_date_till=self.filter_date_till,
            ),
            balance=Balance(
                date_since=self.balance_date_since,
                date_till=self.balance_date_till,
                account_number=self.balance_account_number,
                initial_balance=self.balance_initial_balance,
                total_income=self.balance_total_income,
                total_expense=self.balance_total_expense,
                final_balance=self.balance_final_balance
            ),
            documents=documents or []
        )


class DjangoDocument(models.Model):
    """
    Базовая абстрактная Django-модель для сохранения платежного документа из формата 1CClientBankExchange
    """

    class Meta:
        abstract = True

    document_type = models.TextField(null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    receipt_date = models.DateField(null=True, blank=True)
    receipt_time = models.TimeField(null=True, blank=True)
    receipt_content = models.TextField(null=True, blank=True)

    payer_account = models.CharField(max_length=20, null=True, blank=True)
    payer_date_charged = models.DateField(null=True, blank=True)
    payer_name = models.TextField(null=True, blank=True)
    payer_inn = models.CharField(max_length=12, null=True, blank=True)
    payer_l1_name = models.TextField(null=True, blank=True)
    payer_l2_account_number = models.TextField(null=True, blank=True)
    payer_l3_bank = models.TextField(null=True, blank=True)
    payer_l4_city = models.TextField(null=True, blank=True)
    payer_account_number = models.CharField(max_length=20, null=True, blank=True)
    payer_bank_1_name = models.TextField(null=True, blank=True)
    payer_bank_2_city = models.TextField(null=True, blank=True)
    payer_bank_bic = models.CharField(max_length=9, null=True, blank=True)
    payer_bank_corr_account = models.CharField(max_length=20, null=True, blank=True)

    receiver_account = models.CharField(max_length=20, null=True, blank=True)
    receiver_date_received = models.DateField(null=True, blank=True)
    receiver_name = models.TextField(null=True, blank=True)
    receiver_inn = models.CharField(max_length=12, null=True, blank=True)
    receiver_l1_name = models.TextField(null=True, blank=True)
    receiver_l2_account_number = models.TextField(null=True, blank=True)
    receiver_l3_bank = models.TextField(null=True, blank=True)
    receiver_l4_city = models.TextField(null=True, blank=True)
    receiver_account_number = models.CharField(max_length=20, null=True, blank=True)
    receiver_bank_1_name = models.TextField(null=True, blank=True)
    receiver_bank_2_city = models.TextField(null=True, blank=True)
    receiver_bank_bic = models.CharField(max_length=9, null=True, blank=True)
    receiver_bank_corr_account = models.CharField(max_length=20, null=True, blank=True)

    payment_payment_type = models.TextField(null=True, blank=True)
    payment_operation_type = models.CharField(max_length=2, null=True, blank=True)
    payment_code = models.CharField(max_length=25, null=True, blank=True)
    payment_purpose = models.TextField(null=True, blank=True)
    payment_purpose_l1 = models.TextField(null=True, blank=True)
    payment_purpose_l2 = models.TextField(null=True, blank=True)
    payment_purpose_l3 = models.TextField(null=True, blank=True)
    payment_purpose_l4 = models.TextField(null=True, blank=True)
    payment_purpose_l5 = models.TextField(null=True, blank=True)
    payment_purpose_l6 = models.TextField(null=True, blank=True)

    tax_originator_status = models.CharField(max_length=2, null=True, blank=True)
    tax_payer_kpp = models.CharField(max_length=9, null=True, blank=True)
    tax_receiver_kpp = models.CharField(max_length=9, null=True, blank=True)
    tax_kbk = models.CharField(max_length=20, null=True, blank=True)
    tax_okato = models.CharField(max_length=11, null=True, blank=True)
    tax_basis = models.CharField(max_length=2, null=True, blank=True)
    tax_period = models.CharField(max_length=10, null=True, blank=True)
    tax_number = models.TextField(null=True, blank=True)
    tax_date = models.TextField(null=True, blank=True)
    tax_type = models.TextField(null=True, blank=True)

    special_priority = models.CharField(max_length=2, null=True, blank=True)
    special_term_of_acceptance = models.TextField(null=True, blank=True)
    special_letter_of_credit_type = models.TextField(null=True, blank=True)
    special_maturity = models.TextField(null=True, blank=True)
    special_payment_condition_1 = models.TextField(null=True, blank=True)
    special_payment_condition_2 = models.TextField(null=True, blank=True)
    special_payment_condition_3 = models.TextField(null=True, blank=True)
    special_by_submission = models.TextField(null=True, blank=True)
    special_extra_conditions = models.TextField(null=True, blank=True)
    special_supplier_account_number = models.TextField(null=True, blank=True)
    special_docs_sent_date = models.TextField(null=True, blank=True)

    @classmethod
    def from_document(cls, document: Document):
        return cls(
            document_type=document.document_type,
            number=document.number,
            date=document.date,
            amount=document.amount,

            receipt_date=document.receipt.date,
            receipt_time=document.receipt.time,
            receipt_content=document.receipt.content,

            payer_account=document.payer.account,
            payer_date_charged=document.payer.date_charged,
            payer_name=document.payer.name,
            payer_inn=document.payer.inn,
            payer_l1_name=document.payer.l1_name,
            payer_l2_account_number=document.payer.l2_account_number,
            payer_l3_bank=document.payer.l3_bank,
            payer_l4_city=document.payer.l4_city,
            payer_account_number=document.payer.account_number,
            payer_bank_1_name=document.payer.bank_1_name,
            payer_bank_2_city=document.payer.bank_2_city,
            payer_bank_bic=document.payer.bank_bic,
            payer_bank_corr_account=document.payer.bank_corr_account,

            receiver_account=document.receiver.account,
            receiver_date_received=document.receiver.date_received,
            receiver_name=document.receiver.name,
            receiver_inn=document.receiver.inn,
            receiver_l1_name=document.receiver.l1_name,
            receiver_l2_account_number=document.receiver.l2_account_number,
            receiver_l3_bank=document.receiver.l3_bank,
            receiver_l4_city=document.receiver.l4_city,
            receiver_account_number=document.receiver.account_number,
            receiver_bank_1_name=document.receiver.bank_1_name,
            receiver_bank_2_city=document.receiver.bank_2_city,
            receiver_bank_bic=document.receiver.bank_bic,
            receiver_bank_corr_account=document.receiver.bank_corr_account,

            payment_payment_type=document.payment.payment_type,
            payment_operation_type=document.payment.operation_type,
            payment_code=document.payment.code,
            payment_purpose=document.payment.purpose,
            payment_purpose_l1=document.payment.purpose_l1,
            payment_purpose_l2=document.payment.purpose_l2,
            payment_purpose_l3=document.payment.purpose_l3,
            payment_purpose_l4=document.payment.purpose_l4,
            payment_purpose_l5=document.payment.purpose_l5,
            payment_purpose_l6=document.payment.purpose_l6,

            tax_originator_status=document.tax.originator_status,
            tax_payer_kpp=document.tax.payer_kpp,
            tax_receiver_kpp=document.tax.receiver_kpp,
            tax_kbk=document.tax.kbk,
            tax_okato=document.tax.okato,
            tax_basis=document.tax.basis,
            tax_period=document.tax.period,
            tax_number=document.tax.number,
            tax_date=document.tax.date,
            tax_type=document.tax.type,

            special_priority=document.special.priority,
            special_term_of_acceptance=document.special.term_of_acceptance,
            special_letter_of_credit_type=document.special.letter_of_credit_type,
            special_maturity=document.special.maturity,
            special_payment_condition_1=document.special.payment_condition_1,
            special_payment_condition_2=document.special.payment_condition_2,
            special_payment_condition_3=document.special.payment_condition_3,
            special_by_submission=document.special.by_submission,
            special_extra_conditions=document.special.extra_conditions,
            special_supplier_account_number=document.special.supplier_account_number,
            special_docs_sent_date=document.special.docs_sent_date
        )

    # noinspection PyTypeChecker
    def to_document(self):
        return Document(
            document_type=self.document_type,
            number=self.number,
            date=self.date,
            amount=self.amount,
            receipt=Receipt(
                date=self.receipt_date,
                time=self.receipt_time,
                content=self.receipt_content,
            ),
            payer=Payer(
                account=self.payer_account,
                date_charged=self.payer_date_charged,
                name=self.payer_name,
                inn=self.payer_inn,
                l1_name=self.payer_l1_name,
                l2_account_number=self.payer_l2_account_number,
                l3_bank=self.payer_l3_bank,
                l4_city=self.payer_l4_city,
                account_number=self.payer_account_number,
                bank_1_name=self.payer_bank_1_name,
                bank_2_city=self.payer_bank_2_city,
                bank_bic=self.payer_bank_bic,
                bank_corr_account=self.payer_bank_corr_account,
            ),
            receiver=Receiver(
                account=self.receiver_account,
                date_received=self.receiver_date_received,
                name=self.receiver_name,
                inn=self.receiver_inn,
                l1_name=self.receiver_l1_name,
                l2_account_number=self.receiver_l2_account_number,
                l3_bank=self.receiver_l3_bank,
                l4_city=self.receiver_l4_city,
                account_number=self.receiver_account_number,
                bank_1_name=self.receiver_bank_1_name,
                bank_2_city=self.receiver_bank_2_city,
                bank_bic=self.receiver_bank_bic,
                bank_corr_account=self.receiver_bank_corr_account,
            ),
            payment=Payment(
                payment_type=self.payment_payment_type,
                operation_type=self.payment_operation_type,
                code=self.payment_code,
                purpose=self.payment_purpose,
                purpose_l1=self.payment_purpose_l1,
                purpose_l2=self.payment_purpose_l2,
                purpose_l3=self.payment_purpose_l3,
                purpose_l4=self.payment_purpose_l4,
                purpose_l5=self.payment_purpose_l5,
                purpose_l6=self.payment_purpose_l6,
            ),
            tax=Tax(
                originator_status=self.tax_originator_status,
                payer_kpp=self.tax_payer_kpp,
                receiver_kpp=self.tax_receiver_kpp,
                kbk=self.tax_kbk,
                okato=self.tax_okato,
                basis=self.tax_basis,
                period=self.tax_period,
                number=self.tax_number,
                date=self.tax_date,
                type=self.tax_type,
            ),
            special=Special(
                priority=self.special_priority,
                term_of_acceptance=self.special_term_of_acceptance,
                letter_of_credit_type=self.special_letter_of_credit_type,
                maturity=self.special_maturity,
                payment_condition_1=self.special_payment_condition_1,
                payment_condition_2=self.special_payment_condition_2,
                payment_condition_3=self.special_payment_condition_3,
                by_submission=self.special_by_submission,
                extra_conditions=self.special_extra_conditions,
                supplier_account_number=self.special_supplier_account_number,
                docs_sent_date=self.special_docs_sent_date
            )
        )
