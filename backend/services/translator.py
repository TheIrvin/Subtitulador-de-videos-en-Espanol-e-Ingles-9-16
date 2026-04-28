from functools import lru_cache
from pathlib import Path
import os
import re
import unicodedata


class MissingTranslationPackageError(RuntimeError):
    pass


SOURCE_LANGUAGE = "es"
TARGET_LANGUAGE = "en"
MARIAN_MODEL_NAME = "Helsinki-NLP/opus-mt-es-en"

ARGOS_ROOT = Path(__file__).resolve().parents[1] / "argos"
ARGOS_DATA_DIR = ARGOS_ROOT / "data"
ARGOS_CONFIG_DIR = ARGOS_ROOT / "config"
ARGOS_CACHE_DIR = ARGOS_ROOT / "cache"

SUSPICIOUS_TRANSLATIONS = {
    "THAT'S WHAT I'M TALKING ABOUT.",
    "THATS WHAT IM TALKING ABOUT.",
    "I'M GOING TO TALK ABOUT IT.",
    "IM GOING TO TALK ABOUT IT.",
    "THANK YOU FOR WATCHING.",
}

SUSPICIOUS_PREFIXES = (
    "THAT'S WHAT I",
    "THATS WHAT I",
    "I'M GOING TO TALK",
    "IM GOING TO TALK",
    "THANK YOU FOR",
)

FALLBACK_GLOSSARY = {
    "A": "TO",
    "AL": "TO THE",
    "ANTES": "BEFORE",
    "ARMADURA": "ARMOR",
    "ATRAVIESA": "PIERCES",
    "BALAS": "BULLETS",
    "CHARIOT": "CHARIOT",
    "CON": "WITH",
    "CORTADO": "CUT",
    "CORTARTE": "CUT YOU",
    "CUAL": "WHICH",
    "CUALQUIER": "ANY",
    "CUANDO": "WHEN",
    "CUERPO": "BODY",
    "DE": "OF",
    "DEDICACION": "DEDICATION",
    "DEMUESTRA": "SHOWS",
    "DESDE": "FROM",
    "DESVIAR": "DEFLECT",
    "DIRECCIONES": "DIRECTIONS",
    "DONDE": "WHERE",
    "EL": "THE",
    "EN": "IN",
    "ENEMIGO": "ENEMY",
    "ENTRE": "THE MORE",
    "ENTRENAS": "YOU TRAIN",
    "ES": "IS",
    "ESPADA": "SWORD",
    "FUE": "WAS",
    "GANA": "GAINS",
    "GOLPE": "HIT",
    "HOJA": "BLADE",
    "LA": "THE",
    "LANZAR": "THROW",
    "LO": "IT",
    "MAS": "MORE",
    "MISMO": "SELF",
    "MORTAL": "DEADLY",
    "MOVIENDOSE": "MOVING",
    "MULTIPLES": "MULTIPLE",
    "NI": "NOR",
    "NO": "NO",
    "PARA": "BY",
    "PAREDES": "WALLS",
    "PARPADEAR": "BLINK",
    "PELIGROSO": "DANGEROUS",
    "PERO": "BUT",
    "PIERDE": "LOSES",
    "PODER": "POWER",
    "PROTECCION": "PROTECTION",
    "PROYECTIL": "PROJECTILE",
    "PUEDE": "CAN",
    "PUEDES": "YOU CAN",
    "PUEDAS": "YOU CAN",
    "PASARIA": "WOULD HAPPEN",
    "QUE": "THAT",
    "QU": "WHAT",
    "RAPIDO": "FAST",
    "REACCIONA": "REACTS",
    "REAL": "REAL",
    "REBOTAR": "BOUNCE",
    "RECIBE": "RECEIVES",
    "SABRAN": "WILL KNOW",
    "SE": "IT",
    "SER": "BE",
    "SI": "IF",
    "ESCAPAR": "ESCAPE",
    "SILVER": "SILVER",
    "SIN": "WITHOUT",
    "STAND": "STAND",
    "SU": "ITS",
    "TAN": "SO",
    "TODA": "ALL",
    "TODAS": "ALL",
    "UN": "A",
    "USARA": "USED",
    "VALE": "IS WORTH",
    "VECES": "TIMES",
    "VELOCIDAD": "SPEED",
    "VERDADERO": "TRUE",
    "VIENE": "COMES",
    "VUELVE": "BECOMES",
    "YA": "ALREADY",
    "Y": "AND",
}

COMMON_PHRASES = {
    "QUE": "WHAT",
    "¿QUE": "WHAT",
    "QUE PASARIA SI": "WHAT IF",
    "¿QUE PASARIA SI": "WHAT IF",
    "USARAS": "YOU USED",
    "USARAS SILVER CHARIOT": "YOU HAD SILVER CHARIOT",
    "SILVER CHARIOT": "SILVER CHARIOT",
    "EL STAND QUE": "THE STAND THAT",
    "PUEDE CORTARTE": "CAN CUT YOU",
    "PUEDE CORTARTE ANTES": "CAN CUT YOU BEFORE",
    "DE QUE PUEDAS": "YOU CAN EVEN",
    "PUEDAS PARPADEAR": "YOU CAN BLINK",
    "SE MUEVE": "IT MOVES",
    "TAN RAPIDO": "SO FAST",
    "DESVIAR BALAS": "DEFLECT BULLETS",
    "CON SU ESPADA": "WITH ITS SWORD",
    "MULTIPLES VECES": "MULTIPLE TIMES",
    "PUEDE LANZAR": "CAN LAUNCH",
    "LA HOJA": "THE BLADE",
    "COMO PROYECTIL": "AS A PROJECTILE",
    "REBOTAR EN PAREDES": "BOUNCE OFF WALLS",
    "ATRAVIESA EL CUERPO": "PIERCES THE BODY",
    "DESDE CUALQUIER ANGULO": "FROM ANY ANGLE",
    "AL QUITARSE": "BY REMOVING",
    "LA ARMADURA": "THE ARMOR",
    "GANA VELOCIDAD": "GAINS SPEED",
    "PIERDE TODA PROTECCION": "LOSES ALL PROTECTION",
    "CUALQUIER GOLPE": "ANY HIT",
    "PUEDE SER MORTAL": "CAN BE FATAL",
    "SIN ARMADURA": "WITHOUT ARMOR",
    "PUEDE CREAR": "CAN CREATE",
    "MULTIPLES COPIAS": "MULTIPLE COPIES",
    "DE SI MISMO": "OF ITSELF",
    "EN TODAS DIRECCIONES": "IN EVERY DIRECTION",
    "NO SABRAN": "THEY WILL NOT KNOW",
    "CUAL ES REAL": "WHICH ONE IS REAL",
    "DE DONDE VIENE": "WHERE IT COMES FROM",
    "EL GOLPE VERDADERO": "THE REAL STRIKE",
    "UN STAND": "A STAND",
    "MAS PELIGROSO": "MORE DANGEROUS",
    "SE VUELVE": "BECOMES",
    "CREES QUE": "DO YOU THINK",
    "DEMUESTRA QUE": "PROVES THAT",
    "LA DEDICACION": "DEDICATION",
    "VALE MAS": "IS WORTH MORE",
    "QUE EL PODER": "THAN POWER",
}


def configure_argos_paths() -> None:
    for folder in (ARGOS_DATA_DIR, ARGOS_CONFIG_DIR, ARGOS_CACHE_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("XDG_DATA_HOME", str(ARGOS_DATA_DIR))
    os.environ.setdefault("XDG_CONFIG_HOME", str(ARGOS_CONFIG_DIR))
    os.environ.setdefault("XDG_CACHE_HOME", str(ARGOS_CACHE_DIR))
    os.environ.setdefault("ARGOS_PACKAGES_DIR", str(ARGOS_DATA_DIR / "argos-translate" / "packages"))
    os.environ.setdefault("ARGOS_CHUNK_TYPE", "SPACY")


def repair_mojibake(text: str) -> str:
    raw_text = str(text or "")
    if not any(marker in raw_text for marker in ("Ã", "Â", "�")):
        return raw_text

    try:
        repaired = raw_text.encode("latin1").decode("utf-8")
    except UnicodeError:
        return raw_text

    return repaired if repaired else raw_text


def normalize_source_text(text: str) -> str:
    return re.sub(r"\s+", " ", repair_mojibake(text).strip()).upper()


def normalize_lookup_text(text: str) -> str:
    clean = strip_accents(normalize_source_text(text))
    clean = re.sub(r"[^\w¿?¡!']+", " ", clean, flags=re.UNICODE)
    return re.sub(r"\s+", " ", clean).strip()


def normalize_translation(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().upper())


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def is_translatable_text(text: str) -> bool:
    clean_text = str(text or "").strip()
    if not clean_text:
        return False
    return any(char.isalpha() or char.isdigit() for char in clean_text)


def is_useless_translation(text: str) -> bool:
    normalized = normalize_translation(text)
    if not normalized:
        return True
    return not any(char.isalpha() or char.isdigit() for char in normalized)


def is_suspicious_translation(source_es: str, translated_en: str) -> bool:
    normalized_en = normalize_translation(translated_en)
    normalized_plain = normalized_en.replace("'", "")
    normalized_es = normalize_source_text(source_es)

    if normalized_en in SUSPICIOUS_TRANSLATIONS or normalized_plain in {item.replace("'", "") for item in SUSPICIOUS_TRANSLATIONS}:
        return not any(word in normalized_es for word in ("HABLO", "HABLAR", "GRACIAS", "VER", "MIRAR"))

    if any(normalized_en.startswith(prefix) for prefix in SUSPICIOUS_PREFIXES):
        return not any(word in normalized_es for word in ("HABLO", "HABLAR", "GRACIAS", "VER", "MIRAR"))

    return False


@lru_cache(maxsize=1)
def get_marian_translator():
    try:
        from transformers import MarianMTModel, MarianTokenizer

        tokenizer = MarianTokenizer.from_pretrained(MARIAN_MODEL_NAME, local_files_only=True)
        model = MarianMTModel.from_pretrained(MARIAN_MODEL_NAME, local_files_only=True)
        model.eval()
        return tokenizer, model
    except Exception as exc:
        print(f"Marian local model unavailable: {exc}")
        return None


@lru_cache(maxsize=1)
def get_argos_translation():
    configure_argos_paths()

    from argostranslate import translate

    installed_languages = translate.get_installed_languages()
    source_language = next((language for language in installed_languages if language.code == SOURCE_LANGUAGE), None)
    target_language = next((language for language in installed_languages if language.code == TARGET_LANGUAGE), None)

    if not source_language or not target_language:
        raise MissingTranslationPackageError(
            "Falta instalar el paquete Argos Translate espanol-ingles. "
            "Instala el modelo local con: argospm update; argospm install translate-es_en"
        )

    translation = source_language.get_translation(target_language)
    if not translation:
        raise MissingTranslationPackageError(
            "Falta instalar el paquete Argos Translate espanol-ingles. "
            "Instala el modelo local con: argospm update; argospm install translate-es_en"
        )

    return translation


def translate_with_marian(text_es: str) -> str:
    translator = get_marian_translator()
    if not translator:
        return ""

    tokenizer, model = translator
    inputs = tokenizer([text_es], return_tensors="pt", padding=True, truncation=True, max_length=128)
    output_tokens = model.generate(**inputs, max_new_tokens=64, num_beams=4)
    translated = tokenizer.batch_decode(output_tokens, skip_special_tokens=True)[0]
    return normalize_translation(translated)


def translate_with_argos(text_es: str) -> str:
    translation = get_argos_translation()
    return normalize_translation(translation.translate(text_es))


def fallback_translate_es_to_en(text_es: str) -> str:
    lookup_text = normalize_lookup_text(text_es).strip(" ?!¡")
    if lookup_text in COMMON_PHRASES:
        return normalize_translation(COMMON_PHRASES[lookup_text])

    words = re.findall(r"[A-ZÑ0-9]+", lookup_text)
    translated_words = []

    for word in words:
        key = strip_accents(word)
        translated_words.append(FALLBACK_GLOSSARY.get(key, word))

    return normalize_translation(" ".join(translated_words))


def translate_es_to_en(text_es: str) -> tuple[str, bool]:
    clean_text = normalize_source_text(text_es)
    if not is_translatable_text(clean_text):
        return "", False

    lookup_text = normalize_lookup_text(clean_text).strip(" ?!¡")
    if lookup_text in COMMON_PHRASES:
        return normalize_translation(COMMON_PHRASES[lookup_text]), True

    words = lookup_text.split()
    if 0 < len(words) <= 3:
        fallback = fallback_translate_es_to_en(clean_text)
        if fallback and fallback != normalize_translation(lookup_text):
            return fallback, True

    try:
        translated = translate_with_marian(clean_text)
        if translated and not is_useless_translation(translated) and not is_suspicious_translation(clean_text, translated):
            return translated, False
        print(f"Marian translation unusable: {clean_text} -> {translated}")
    except BaseException as exc:
        print(f"Marian translation failed for '{clean_text}': {exc}")

    try:
        translated = translate_with_argos(clean_text)
        if translated and not is_useless_translation(translated) and not is_suspicious_translation(clean_text, translated):
            return translated, True
        print(f"Argos translation unusable: {clean_text} -> {translated}")
    except BaseException as exc:
        print(f"Argos translation failed for '{clean_text}': {exc}")

    fallback = fallback_translate_es_to_en(clean_text)
    return fallback, True


def translate_text_es_to_en(text: str, translation=None) -> str:
    translated, _warning = translate_es_to_en(text)
    return translated


def translate_blocks(blocks: list[dict]) -> list[dict]:
    translated_blocks = []
    total_blocks = len(blocks)
    blocks_with_text = 0
    translated_count = 0
    failed_count = 0

    for block in blocks:
        translated_block = dict(block)
        block_id = translated_block.get("id", "unknown")
        text_es = normalize_source_text(translated_block.get("text_es", ""))

        if not is_translatable_text(text_es):
            translated_block["text_en"] = ""
            translated_block["translation_warning"] = False
            translated_block["translation_outdated"] = False
            translated_blocks.append(translated_block)
            continue

        blocks_with_text += 1
        print(f"Translating block {block_id}: {text_es}")
        try:
            translated_text, warning = translate_es_to_en(text_es)
        except BaseException as exc:
            print(f"Unexpected translation error for block {block_id}: {text_es} -> {exc}")
            translated_text = fallback_translate_es_to_en(text_es)
            warning = True

        if is_useless_translation(translated_text):
            print(f"Translation failed for block {block_id}: {text_es}")
            translated_block["text_en"] = ""
            translated_block["translation_warning"] = True
            failed_count += 1
        else:
            translated_block["text_en"] = translated_text
            translated_block["translation_warning"] = warning
            translated_count += 1

        translated_block["translation_outdated"] = False
        translated_blocks.append(translated_block)

    print(
        "Translation summary: "
        f"total={total_blocks}, with_text={blocks_with_text}, translated={translated_count}, failed={failed_count}"
    )

    return translated_blocks
