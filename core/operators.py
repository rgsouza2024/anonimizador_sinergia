"""Operator mapping used by Presidio anonymizer."""

from presidio_anonymizer.entities import OperatorConfig


def obter_operadores_anonimizacao():
    return {
        "DEFAULT": OperatorConfig("keep"),
        "PERSON": OperatorConfig("keep"),
        "LOCATION": OperatorConfig("keep"),
        "ENDERECO_LOGRADOURO": OperatorConfig("replace", {"new_value": "<ENDERECO>"}),
        "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
        "PHONE_NUMBER": OperatorConfig("mask", {"type": "mask", "masking_char": "*", "chars_to_mask": 4, "from_end": True}),
        "CPF": OperatorConfig("replace", {"new_value": "<CPF/CIN>"}),
        "DATE_TIME": OperatorConfig("keep"),
        "OAB_NUMBER": OperatorConfig("replace", {"new_value": "<OAB>"}),
        "CEP_NUMBER": OperatorConfig("replace", {"new_value": "<CEP>"}),
        "ESTADO_CIVIL": OperatorConfig("keep"),
        "ORGANIZACAO_CONHECIDA": OperatorConfig("keep"),
        "ID_DOCUMENTO": OperatorConfig("keep"),
        "LEGAL_TITLE": OperatorConfig("keep"),
        "LEGAL_OR_COMMON_TERM": OperatorConfig("keep"),
        "CNH": OperatorConfig("replace", {"new_value": "***********"}),
        "SIAPE": OperatorConfig("replace", {"new_value": "***"}),
        "RG_NUMBER": OperatorConfig("replace", {"new_value": "<NUMERO RG>"}),
        "MATRICULA_SIAPE": OperatorConfig("replace", {"new_value": "***"}),
        "TERMO_COMUM": OperatorConfig("keep"),
    }

