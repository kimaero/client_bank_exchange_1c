import re
from decimal import Decimal
from datetime import date, time, datetime
from enum import Flag, auto, Enum
from functools import reduce
from typing import NamedTuple, List, Callable, Pattern, AnyStr, Any, Optional

DATE_FORMAT = '%d.%m.%Y'
TIME_FORMAT = '%H:%M:%S'


class Required(Flag):
    NONE = 0
    TO_BANK = auto()
    FROM_BANK = auto()
    BOTH = TO_BANK | FROM_BANK


class FieldType(NamedTuple):
    type: type
    cast_from_text: Callable
    cast_to_text: Callable


class Cast:
    @staticmethod
    def str_to_text(obj: AnyStr) -> Optional[str]:
        """
        Конвертирует строку из 1CClientBankExchange в чистую строку или None

        :param obj: строка
        :return: строка или None
        """
        if obj and obj.strip():
            return obj.strip()
        else:
            return None

    @staticmethod
    def str_to_date(obj: AnyStr) -> Optional[date]:
        """
        Конвертирует строку из 1CClientBankExchange в дату

        :param obj: строка в формате *дд.мм.гггг*
        :return: datetime.date
        """
        if obj:
            return datetime.strptime(obj, DATE_FORMAT).date()
        else:
            return None

    @staticmethod
    def str_to_time(obj: AnyStr) -> Optional[time]:
        """
        Конвертирует строку из 1CClientBankExchange во время

        :param obj: строка в формате *чч:мм:сс*
        :return: datetime.time
        """
        if obj:
            return datetime.strptime(obj, TIME_FORMAT).time()
        else:
            return None

    @staticmethod
    def str_to_amount(obj: AnyStr) -> Decimal:
        """
        Конвертирует строку из 1CClientBankExchange в Decimal

        :param obj: строка в формате руб[.коп]
        :return: decimal.Decimal
        """
        return Decimal(
            re.sub(r'[^0-9,.\-]', '', str(obj))
                .replace("'", '')
                .replace(' ', '')
                .replace(',', '.')
                .replace('.', '', obj.count('.') - 1)
        )

    @staticmethod
    def text_to_str(obj: AnyStr) -> str:
        """
        Конвертирует чистую строку в строку 1CClientBankExchange

        :param obj: строка или None
        :return: строка
        """
        if obj:
            return str(obj).strip()
        else:
            return ''

    @staticmethod
    def date_to_str(obj: Optional[date]) -> str:
        """
        Конвертирует дату в строку

        :param obj: datetime.date
        :return: строка в формате *дд.мм.гггг*
        """
        if obj:
            return obj.strftime(DATE_FORMAT)
        else:
            return ''

    @staticmethod
    def time_to_str(obj: Optional[time]) -> str:
        """
        Конвертирует время в строку

        :param obj: datetime.time
        :return: строка в формате *чч:мм:сс*
        """
        if obj:
            return obj.strftime(TIME_FORMAT)
        else:
            return ''

    @staticmethod
    def amount_to_str(obj: Optional[Decimal]) -> str:
        """
        Конвертирует Decimal в строку

        :param obj: decimal.Decimal
        :return: строка в формате руб[.коп]
        """
        return str(obj).replace(',', '.')


class Type(Enum):
    TEXT = FieldType(type=str, cast_from_text=Cast.str_to_text, cast_to_text=Cast.text_to_str)
    DATE = FieldType(type=date, cast_from_text=Cast.str_to_date, cast_to_text=Cast.date_to_str)
    TIME = FieldType(type=time, cast_from_text=Cast.str_to_time, cast_to_text=Cast.time_to_str)
    AMOUNT = FieldType(type=Decimal, cast_from_text=Cast.str_to_amount, cast_to_text=Cast.amount_to_str)
    ARRAY = FieldType(type=List[str], cast_from_text=Cast.str_to_text, cast_to_text=Cast.text_to_str)
    FLAG = FieldType(type=type(None), cast_from_text=Cast.str_to_text, cast_to_text=Cast.text_to_str)


class Field(NamedTuple):
    key: str
    description: str
    required: Required = Required.NONE
    type: Type = Type.TEXT

    def get_value_from_text(self, source_text: AnyStr) -> Any:
        regex = r'^' + self.key + '=(.*?)$'
        found = re.findall(regex, source_text, re.MULTILINE)

        if len(found) > 1 and self.type != Type.ARRAY:
            raise ValueError(f'Согласно спецификации {self.key} не может быть несколькими строками, однако найдено '
                             f'{len(found)} шт.')

        if not found:
            return None
        elif self.type == Type.ARRAY and len(found) > 1:
            return [self.type.value.cast_from_text(item) for item in found]
        else:
            return self.type.value.cast_from_text(found[0])


class Schema:
    @classmethod
    def to_dict(cls) -> dict:
        return {
            attr: getattr(cls, attr)
            for attr in cls.__dict__.keys() if not attr.startswith("__")
        }


class Section:
    class Meta(NamedTuple):
        regex: Pattern[str] = None

    @classmethod
    def extract_section_text(cls, source_text: AnyStr):
        regex = cls.Meta.regex

        if not regex:
            raise ValueError('Regex для секции не определен: нет смысла парсить подсекции')

        result = regex.findall(source_text)
        if result:
            if len(result) == 1:
                return result[0]
            else:
                return result

    @classmethod
    def from_text(cls, section_text):
        obj = cls()
        for key, field in cls.Schema.to_dict().items():
            value = field.get_value_from_text(section_text)
            setattr(obj, key, value)
        return obj

    def to_text(self, validate=True):

        # noinspection PyShadowingNames
        def get_text(key, field, attr):
            # noinspection PyShadowingNames
            def get_line(key, field, attr):
                is_flag = field.type == Type.FLAG
                name = field.key
                value = field.type.value.cast_to_text(attr)
                required = Required.TO_BANK in field.required
                if not required and not value:
                    return ''
                else:
                    return f'{name}' if is_flag else f'{name}={value}'

            if attr and field.type == Type.ARRAY:
                lines = [get_line(key, field, item) for item in attr]
                return '\n'.join(lines) if lines else ''
            else:
                return get_line(key, field, attr)

        # noinspection PyShadowingNames
        def validate_attr(key, field, attr):
            is_flag = field.type == Type.FLAG
            name = field.key
            value = field.type.value.cast_to_text(attr)
            required = Required.TO_BANK in field.required
            if required and not is_flag and not value:
                raise ValueError(f'Обязательны при отправке в банк аттрибут {name} не содержит значения!')

        result = []
        for key, field in self.__class__.Schema.to_dict().items():
            attr = getattr(self, key, None)
            if validate:
                validate_attr(key, field, attr)
            text = get_text(key, field, attr)
            result.append(text)

        return '\n'.join(filter(lambda x: x != '', result))

    def __str__(self):
        return self.to_text(validate=False)


class Header(Section):
    """
    Секция заголовка файла, описывает формат, версию, кодировку, программы отправителя и получателя,
    сведения об условиях отбора передаваемых данных
    """

    class Meta(NamedTuple):
        regex = re.compile(r'^(.*?)Секция', re.S)

    class Schema(Schema):
        format_name = Field('1CClientBankExchange', 'Внутренний признак файла обмена', Required.BOTH, type=Type.FLAG)
        format_version = Field('ВерсияФормата', 'Номер версии формата обмена', Required.BOTH)
        encoding = Field('Кодировка', 'Кодировка файла', Required.BOTH)
        sender = Field('Отправитель', 'Программа-отправитель', Required.TO_BANK)
        receiver = Field('Получатель', 'Программа-получатель', Required.FROM_BANK)
        creation_date = Field('ДатаСоздания', 'Дата формирования файла', type=Type.DATE)
        creation_time = Field('ВремяСоздания', 'Время формирования файла', type=Type.TIME)
        filter_date_since = Field('ДатаНачала', 'Дата начала интервала', Required.BOTH, type=Type.DATE)
        filter_date_till = Field('ДатаКонца', 'Дата конца интервала', Required.BOTH, type=Type.DATE)
        filter_account_numbers = Field('РасчСчет', 'Расчетный счет организации', Required.BOTH, type=Type.ARRAY)
        filter_document_types = Field('Документ', 'Вид документа', type=Type.ARRAY)

    def __init__(self, format_name: str = None, format_version: str = None, encoding: str = None, sender: str = None,
                 receiver: str = None, creation_date: Type.DATE.value.type = None,
                 creation_time: Type.TIME.value.type = None, filter_date_since: Type.DATE.value.type = None,
                 filter_date_till: Type.DATE.value.type = None, filter_account_numbers: Type.ARRAY.value.type = None,
                 filter_document_types: Type.ARRAY.value.type = None):
        super(Header, self).__init__()
        self.format_name = format_name
        self.format_version = format_version
        self.encoding = encoding
        self.sender = sender
        self.receiver = receiver
        self.creation_date = creation_date
        self.creation_time = creation_time
        self.filter_date_since = filter_date_since
        self.filter_date_till = filter_date_till
        self.filter_account_numbers = filter_account_numbers
        self.filter_document_types = filter_document_types

    @classmethod
    def from_text(cls, source_text):
        section_text = cls.extract_section_text(source_text)
        return super().from_text(section_text)


class Balance(Section):
    """
    Секция передачи остатков по расчетному счету
    """

    class Meta(NamedTuple):
        regex = re.compile(r'СекцияРасчСчет(.*?)КонецРасчСчет', re.S)

    class Schema(Schema):
        tag_begin = Field('СекцияРасчСчет', 'Признак начала секции', type=Type.FLAG)
        date_since = Field('ДатаНачала', 'Дата начала интервала', Required.FROM_BANK, type=Type.DATE)
        date_till = Field('ДатаКонца', 'Дата конца интервала', type=Type.DATE)
        account_number = Field('РасчСчет', 'Расчетный счет организации', Required.FROM_BANK)
        initial_balance = Field('НачальныйОстаток', 'Начальный остаток', Required.FROM_BANK, type=Type.AMOUNT)
        total_income = Field('ВсегоПоступило', 'Обороты входящих платежей', type=Type.AMOUNT)
        total_expense = Field('ВсегоСписано', 'Обороты исходящих платежей', type=Type.AMOUNT)
        final_balance = Field('КонечныйОстаток', 'Конечный остаток', type=Type.AMOUNT)
        tag_end = Field('КонецРасчСчет', 'Признак окончания секции', type=Type.FLAG)

    def __init__(self, tag_begin: str = None, date_since: Type.DATE.value.type = None,
                 date_till: Type.DATE.value.type = None, account_number: str = None,
                 initial_balance: Type.AMOUNT.value.type = None, total_income: Type.AMOUNT.value.type = None,
                 total_expense: Type.AMOUNT.value.type = None, final_balance: Type.AMOUNT.value.type = None,
                 tag_end: str = None):
        super(Balance, self).__init__()
        self.tag_begin = tag_begin
        self.date_since = date_since
        self.date_till = date_till
        self.account_number = account_number
        self.initial_balance = initial_balance
        self.total_income = total_income
        self.total_expense = total_expense
        self.final_balance = final_balance
        self.tag_end = tag_end

    def to_text(self, validate=True):
        content = super(Balance, self).to_text(validate=validate)
        return f'СекцияРасчСчет\n{content}\nКонецРасчСчет'

    @classmethod
    def from_text(cls, source_text):
        section_text = cls.extract_section_text(source_text)
        return super().from_text(section_text)


class Receipt(Section):
    """
    Квитанция по платежному документу
    """

    class Schema(Schema):
        date = Field('КвитанцияДата', 'Дата формирования квитанции', type=Type.DATE)
        time = Field('КвитанцияВремя', 'Время формирования квитанции', type=Type.TIME)
        content = Field('КвитанцияСодержание', 'Содержание квитанции')

    # noinspection PyShadowingNames
    def __init__(self, date: Type.DATE.value.type = None, time: Type.TIME.value.type = None, content: str = None):
        super(Receipt, self).__init__()
        self.date = date
        self.time = time
        self.content = content


class Payer(Section):
    """
    Реквизиты плательщика
    """

    class Meta(NamedTuple):
        regex = None

    class Schema(Schema):
        account = Field('ПлательщикСчет', 'Расчетный счет плательщика', Required.BOTH)
        date_charged = Field('ДатаСписано', 'Дата списания средств с р/с', Required.FROM_BANK, type=Type.DATE)
        name = Field('Плательщик', 'Плательщик', Required.TO_BANK)
        inn = Field('ПлательщикИНН', 'ИНН плательщика', Required.BOTH)
        l1_name = Field('Плательщик1', 'Наименование плательщика, стр. 1', Required.TO_BANK)
        l2_account_number = Field('Плательщик2', 'Наименование плательщика, стр. 2')
        l3_bank = Field('Плательщик3', 'Наименование плательщика, стр. 3')
        l4_city = Field('Плательщик4', 'Наименование плательщика, стр. 4')
        account_number = Field('ПлательщикРасчСчет', 'Расчетный счет плательщика', Required.TO_BANK)
        bank_1_name = Field('ПлательщикБанк1', 'Банк плательщика', Required.TO_BANK)
        bank_2_city = Field('ПлательщикБанк2', 'Город банка плательщика', Required.TO_BANK)
        bank_bic = Field('ПлательщикБИК', 'БИК банка плательщика', Required.TO_BANK)
        bank_corr_account = Field('ПлательщикКорсчет', 'Корсчет банка плательщика', Required.TO_BANK)

    def __init__(self, account: str = None, date_charged: Type.DATE.value.type = None, name: str = None,
                 inn: str = None, l1_name: str = None, l2_account_number: str = None, l3_bank: str = None,
                 l4_city: str = None, account_number: str = None, bank_1_name: str = None, bank_2_city: str = None,
                 bank_bic: str = None, bank_corr_account: str = None):
        super(Payer, self).__init__()
        self.account = account
        self.date_charged = date_charged
        self.name = name
        self.inn = inn
        self.l1_name = l1_name
        self.l2_account_number = l2_account_number
        self.l3_bank = l3_bank
        self.l4_city = l4_city
        self.account_number = account_number
        self.bank_1_name = bank_1_name
        self.bank_2_city = bank_2_city
        self.bank_bic = bank_bic
        self.bank_corr_account = bank_corr_account


class Receiver(Section):
    """
    Реквизиты получателя
    """

    class Meta(NamedTuple):
        regex = None

    class Schema(Schema):
        account = Field('ПолучательСчет', 'Расчетный счет получателя', Required.BOTH)
        date_received = Field('ДатаПоступило', 'Дата поступления средств на р/с', Required.FROM_BANK)
        name = Field('Получатель', 'Получатель', Required.TO_BANK)
        inn = Field('ПолучательИНН', 'ИНН получателя', Required.BOTH)
        l1_name = Field('Получатель1', 'Наименование получателя', Required.TO_BANK)
        l2_account_number = Field('Получатель2', 'Наименование получателя, стр. 2')
        l3_bank = Field('Получатель3', 'Наименование получателя, стр. 3')
        l4_city = Field('Получатель4', 'Наименование получателя, стр. 4')
        account_number = Field('ПолучательРасчСчет', 'Расчетный счет получателя', Required.TO_BANK)
        bank_1_name = Field('ПолучательБанк1', 'Банк получателя', Required.TO_BANK)
        bank_2_city = Field('ПолучательБанк2', 'Город банка получателя', Required.TO_BANK)
        bank_bic = Field('ПолучательБИК', 'БИК банка получателя', Required.TO_BANK)
        bank_corr_account = Field('ПолучательКорсчет', 'Корсчет банка получателя', Required.TO_BANK)

    def __init__(self, account: str = None, date_received: str = None, name: str = None, inn: str = None,
                 l1_name: str = None, l2_account_number: str = None, l3_bank: str = None, l4_city: str = None,
                 account_number: str = None, bank_1_name: str = None, bank_2_city: str = None, bank_bic: str = None,
                 bank_corr_account: str = None):
        super(Receiver, self).__init__()
        self.account = account
        self.date_received = date_received
        self.name = name
        self.inn = inn
        self.l1_name = l1_name
        self.l2_account_number = l2_account_number
        self.l3_bank = l3_bank
        self.l4_city = l4_city
        self.account_number = account_number
        self.bank_1_name = bank_1_name
        self.bank_2_city = bank_2_city
        self.bank_bic = bank_bic
        self.bank_corr_account = bank_corr_account


class Payment(Section):
    """
    Реквизиты платежа
    """

    class Meta(NamedTuple):
        regex = None

    class Schema(Schema):
        payment_type = Field('ВидПлатежа', 'Вид платежа')
        operation_type = Field('ВидОплаты', 'Вид оплаты (вид операции)', Required.TO_BANK)
        code = Field('Код', 'Уникальный идентификатор платежа')
        purpose = Field('НазначениеПлатежа', 'Назначение платежа')
        purpose_l1 = Field('НазначениеПлатежа1', 'Назначение платежа, стр. 1')
        purpose_l2 = Field('НазначениеПлатежа2', 'Назначение платежа, стр. 2')
        purpose_l3 = Field('НазначениеПлатежа3', 'Назначение платежа, стр. 3')
        purpose_l4 = Field('НазначениеПлатежа4', 'Назначение платежа, стр. 4')
        purpose_l5 = Field('НазначениеПлатежа5', 'Назначение платежа, стр. 5')
        purpose_l6 = Field('НазначениеПлатежа6', 'Назначение платежа, стр. 6')

    def __init__(self, payment_type: str = None, operation_type: str = None, code: str = None, purpose: str = None,
                 purpose_l1: str = None, purpose_l2: str = None, purpose_l3: str = None, purpose_l4: str = None,
                 purpose_l5: str = None, purpose_l6: str = None):
        super(Payment, self).__init__()
        self.payment_type = payment_type
        self.operation_type = operation_type
        self.code = code
        self.purpose = purpose
        self.purpose_l1 = purpose_l1
        self.purpose_l2 = purpose_l2
        self.purpose_l3 = purpose_l3
        self.purpose_l4 = purpose_l4
        self.purpose_l5 = purpose_l5
        self.purpose_l6 = purpose_l6


# noinspection PyShadowingBuiltins
class Tax(Section):
    """
    Дополнительные реквизиты для платежей в бюджетную систему Российской Федерации
    """

    class Meta(NamedTuple):
        regex = None

    class Schema(Schema):
        originator_status = Field('СтатусСоставителя', 'Статус составителя расчетного документа', Required.BOTH)
        payer_kpp = Field('ПлательщикКПП', 'КПП плательщика', Required.BOTH)
        receiver_kpp = Field('ПолучательКПП', 'КПП получателя', Required.BOTH)
        kbk = Field('ПоказательКБК', 'Показатель кода бюджетной классификации', Required.BOTH)
        okato = Field('ОКАТО',
                      'Код ОКТМО территории, на которой мобилизуются денежные средства от уплаты налога, сбора и иного '
                      'платежа', Required.BOTH)
        basis = Field('ПоказательОснования', 'Показатель основания налогового платежа', Required.BOTH)
        period = Field('ПоказательПериода', 'Показатель налогового периода / Код таможенного органа', Required.BOTH)
        number = Field('ПоказательНомера', 'Показатель номера документа', Required.BOTH)
        date = Field('ПоказательДаты', 'Показатель даты документа', Required.BOTH)
        type = Field('ПоказательТипа', 'Показатель типа платежа')

    # noinspection PyShadowingNames
    def __init__(self, originator_status: str = None, payer_kpp: str = None, receiver_kpp: str = None, kbk: str = None,
                 okato: str = None, basis: str = None, period: str = None, number: str = None, date: str = None,
                 type: str = None):
        super(Tax, self).__init__()
        self.originator_status = originator_status
        self.payer_kpp = payer_kpp
        self.receiver_kpp = receiver_kpp
        self.kbk = kbk
        self.okato = okato
        self.basis = basis
        self.period = period
        self.number = number
        self.date = date
        self.type = type


class Special(Section):
    """
    Дополнительные реквизиты для отдельных видов документов
    """

    class Meta(NamedTuple):
        regex = None

    class Schema(Schema):
        priority = Field('Очередность', 'Очередность платежа')
        term_of_acceptance = Field('СрокАкцепта', 'Срок акцепта, количество дней')
        letter_of_credit_type = Field('ВидАккредитива', 'Вид аккредитива')
        maturity = Field('СрокПлатежа', 'Срок платежа (аккредитива)')
        payment_condition_1 = Field('УсловиеОплаты1', 'Условие оплаты, стр. 1')
        payment_condition_2 = Field('УсловиеОплаты2', 'Условие оплаты, стр. 2')
        payment_condition_3 = Field('УсловиеОплаты3', 'Условие оплаты, стр. 3')
        by_submission = Field('ПлатежПоПредст', 'Платеж по представлению')
        extra_conditions = Field('ДополнУсловия', 'Дополнительные условия')
        supplier_account_number = Field('НомерСчетаПоставщика', '№ счета поставщика')
        docs_sent_date = Field('ДатаОтсылкиДок', 'Дата отсылки документов')

    def __init__(self, priority: str = None, term_of_acceptance: str = None, letter_of_credit_type: str = None,
                 maturity: str = None, payment_condition_1: str = None, payment_condition_2: str = None,
                 payment_condition_3: str = None, by_submission: str = None, extra_conditions: str = None,
                 supplier_account_number: str = None, docs_sent_date: str = None):
        super(Special, self).__init__()
        self.priority = priority
        self.term_of_acceptance = term_of_acceptance
        self.letter_of_credit_type = letter_of_credit_type
        self.maturity = maturity
        self.payment_condition_1 = payment_condition_1
        self.payment_condition_2 = payment_condition_2
        self.payment_condition_3 = payment_condition_3
        self.by_submission = by_submission
        self.extra_conditions = extra_conditions
        self.supplier_account_number = supplier_account_number
        self.docs_sent_date = docs_sent_date


class Document(Section):
    """
    Секция платежного документа, содержит шапку платежного документа и подсекции: квитанция, реквизиты
    плательщика и получателя, реквизиты платежа и дополнительные реквизиты для платежей в бюджет и для отдельных
    видов документов
    """

    class Meta(NamedTuple):
        regex = re.compile(r'(СекцияДокумент.*?)КонецДокумента', re.S)

    class Schema(Schema):
        document_type = Field('СекцияДокумент', 'Признак начала секции')  # содержит вид документа
        number = Field('Номер', 'Номер документа', Required.BOTH)
        date = Field('Дата', 'Дата документа', Required.BOTH, type=Type.DATE)
        amount = Field('Сумма', 'Сумма платежа', Required.BOTH, type=Type.AMOUNT)

    class Subsections(Schema):
        receipt = Receipt
        payer = Payer
        receiver = Receiver
        payment = Payment
        tax = Tax
        special = Special

    # noinspection PyShadowingNames
    def __init__(self, document_type: str = None, number: str = None, date: Type.DATE.value.type = None,
                 amount: str = None, receipt: Receipt = None, payer: Payer = None, receiver: Receiver = None,
                 payment: Payment = None, tax: Tax = None, special: Special = None):
        super(Document, self).__init__()
        self.document_type = document_type
        self.number = number
        self.date = date
        self.amount = amount
        self.receipt = receipt
        self.payer = payer
        self.receiver = receiver
        self.payment = payment
        self.tax = tax
        self.special = special

    @classmethod
    def from_text(cls, source_text: AnyStr):
        extracted = cls.extract_section_text(source_text)

        if not isinstance(extracted, list):
            extracted = [extracted]

        results = []
        for section_text in extracted:
            obj: cls = super().from_text(section_text)
            obj.receipt = Receipt.from_text(section_text)
            obj.payer = Payer.from_text(section_text)
            obj.receiver = Receiver.from_text(section_text)
            obj.payment = Payment.from_text(section_text)
            obj.tax = Tax.from_text(section_text)
            obj.special = Special.from_text(section_text)
            results.append(obj)

        return results

    def to_text(self, validate=True):
        content = super(Document, self).to_text(validate=validate)
        sections = list(filter(None, [self.receipt, self.payer, self.receiver, self.payment, self.tax, self.special]))
        sections = list(map(lambda x: str(x), sections))
        sections.append('КонецДокумента')
        return content + '\n' + '\n'.join(sections)


class Statement:
    def __init__(self, header: Header, balance: Balance = None, documents: List[Document] = None):
        super(Statement, self).__init__()
        self.header: Header = header
        self.balance: Balance = balance
        self.documents: List[Document] = documents

    @classmethod
    def from_file(cls, filename: str):
        """
        Конструктор полного документа выписки из файла

        :param filename: Путь к файлу
        :return: Заполненный объект полного документа выписки
        """
        text = open(filename, encoding='cp1251').read()
        return cls.from_text(text)

    @classmethod
    def from_text(cls, source_text):
        """
        Конструктор полного документа выписки из текста файла

        :param source_text: Полный текст файла выписки в формате 1CClientBankExchange
        :return: Заполненный объект полного документа выписки
        """

        # return source_text
        return cls(
            header=Header.from_text(source_text),
            balance=Balance.from_text(source_text),
            documents=Document.from_text(source_text)
        )

    @classmethod
    def from_documents(cls, sender: str, documents: List[Document]):
        payments_from_the_only_bank = len(set([d.payer.bank_bic for d in documents])) == 1
        if not payments_from_the_only_bank:
            raise ValueError('Файл для загрузки в банк должен содержать платежи только из одного банка!')

        dates = [doc.date for doc in documents]

        return cls(
            header=Header(
                format_version='1.02',
                encoding='Windows',
                sender=sender,
                creation_date=date.today(),
                creation_time=datetime.now(),
                filter_date_since=min(dates),
                filter_date_till=max(dates),
                filter_account_numbers=set([d.payer.account_number for d in documents])
            ),
            balance=None,
            documents=documents
        )

    def to_text(self, validate=True):
        results = [
            self.header.to_text(validate=validate),
            self.balance.to_text(validate=validate) if self.balance else None
        ]

        if self.documents:
            results.extend([doc.to_text(validate=validate) for doc in self.documents])

        results.append('КонецФайла')

        return '\n\n'.join(filter(lambda x: x, results))

    def __str__(self):
        return self.to_text(validate=False)

    def count(self):
        return len(self.documents)

    def total_amount(self):
        return reduce(lambda x, y: x + y, [doc.amount for doc in self.documents]) if self.documents else 0
