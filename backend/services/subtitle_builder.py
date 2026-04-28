import re
import unicodedata


WORDS_PER_BLOCK = 3
VOICE_GAP_SECONDS = 0.75
SUBTITLE_LEAD_SECONDS = 0.12
VIDEO_WIDTH = 1080
SUBTITLE_SAFE_WIDTH_RATIO = 0.86
DEFAULT_FONT_SIZE_ES = 64
DEFAULT_FONT_SIZE_EN = 70
DEFAULT_Y_ES = 1540
DEFAULT_Y_EN = 1440
EN_FONT_SIZE = DEFAULT_FONT_SIZE_EN
ES_FONT_SIZE = DEFAULT_FONT_SIZE_ES
MAX_EN_VISUAL_WIDTH = VIDEO_WIDTH * SUBTITLE_SAFE_WIDTH_RATIO
MAX_ES_VISUAL_WIDTH = VIDEO_WIDTH * 0.9


def build_words_for_block(text: str, start: float, end: float) -> list[dict]:
    words = str(text or "").split()
    if not words:
        return []

    duration = max(float(end) - float(start), 0.01)
    seconds_per_word = duration / len(words)

    return [
        {
            "word": word.upper(),
            "start": round(float(start) + (index * seconds_per_word), 2),
            "end": round(float(start) + ((index + 1) * seconds_per_word), 2),
        }
        for index, word in enumerate(words)
    ]


def refresh_block_words(block: dict) -> dict:
    refreshed = dict(block)
    refreshed["text_es"] = refreshed.get("text_es", "").upper()
    refreshed["words"] = build_words_for_block(refreshed["text_es"], refreshed.get("start", 0), refreshed.get("end", 0))
    refreshed["x"] = refreshed.get("x", 540)
    return refreshed


def split_text_words(text: str) -> list[str]:
    return re.sub(r"\s+", " ", str(text or "").strip()).split()


def normalize_match_word(word: str) -> str:
    normalized = unicodedata.normalize("NFD", str(word or "").lower())
    without_accents = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", without_accents)


def text_match_words(text: str) -> list[str]:
    return [word for word in (normalize_match_word(word) for word in split_text_words(text)) if word]


def split_text_paragraphs(text: str) -> list[str]:
    normalized = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    return [re.sub(r"\s+", " ", paragraph).strip() for paragraph in re.split(r"\n\s*\n+", normalized) if paragraph.strip()]


def chunk_words(words: list[str], words_per_block: int = WORDS_PER_BLOCK) -> list[list[str]]:
    return [words[index : index + words_per_block] for index in range(0, len(words), words_per_block)]


def chunk_words_into_count(words: list[str], count: int) -> list[list[str]]:
    if count <= 0:
        return []
    if not words:
        return [[] for _ in range(count)]

    chunks = []
    total_words = len(words)
    for index in range(count):
        start = round(index * total_words / count)
        end = round((index + 1) * total_words / count)
        chunks.append(words[start:end])
    return chunks


def estimate_word_width(word: str, font_size: int = EN_FONT_SIZE) -> float:
    width = 0.0
    for char in str(word or ""):
        if char in "ilI.,'!|":
            width += 0.28
        elif char in "mwMW@#%&":
            width += 0.92
        elif char.isupper():
            width += 0.68
        else:
            width += 0.58
    return max(width * font_size, font_size * 0.45)


def estimate_text_width(words: list[str], font_size: int = EN_FONT_SIZE) -> float:
    if not words:
        return 0.0
    spaces_width = max(len(words) - 1, 0) * font_size * 0.32
    return sum(estimate_word_width(word, font_size) for word in words) + spaces_width


def reading_weight(words: list[str]) -> float:
    if not words:
        return 1.0
    visual_weight = estimate_text_width(words) / max(EN_FONT_SIZE, 1)
    return max(len(words), visual_weight / 2.4, 1.0)


def split_oversized_chunk(words: list[str], max_width: float = MAX_EN_VISUAL_WIDTH) -> list[list[str]]:
    if not words:
        return [[]]
    if estimate_text_width(words) <= max_width:
        return [words]

    chunks = []
    current = []
    for word in words:
        candidate = current + [word]
        if current and estimate_text_width(candidate) > max_width:
            chunks.append(current)
            current = [word]
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks


def split_oversized_chunk_for_font(words: list[str], font_size: int, max_width: float) -> list[list[str]]:
    if not words:
        return [[]]
    if estimate_text_width(words, font_size) <= max_width:
        return [words]

    chunks = []
    current = []
    for word in words:
        candidate = current + [word]
        if current and estimate_text_width(candidate, font_size) > max_width:
            chunks.append(current)
            current = [word]
        else:
            current = candidate

    if current:
        chunks.append(current)
    return chunks


def fit_spanish_chunks_to_video(chunks: list[list[str]]) -> list[list[str]]:
    fitted = []
    for chunk in chunks:
        fitted.extend(split_oversized_chunk_for_font(chunk, ES_FONT_SIZE, MAX_ES_VISUAL_WIDTH))
    return fitted


def fit_english_chunks_to_video(chunks: list[list[str]]) -> list[list[str]]:
    fitted = []
    for chunk in chunks:
        fitted.extend(split_oversized_chunk_for_font(chunk, EN_FONT_SIZE, MAX_EN_VISUAL_WIDTH))
    return fitted


def reserve_special_english_chunks(words: list[str]) -> tuple[list[list[str]], list[str]]:
    chunks = []
    remaining = list(words)

    if len(remaining) >= 2 and normalize_match_word(remaining[0]) == "what" and normalize_match_word(remaining[1]) == "if":
        chunks.append(remaining[:2])
        remaining = remaining[2:]

    if len(remaining) >= 2 and normalize_match_word(remaining[0]) == "you" and normalize_match_word(remaining[1]) == "had":
        chunks.append(remaining[:2])
        remaining = remaining[2:]

        name_words = []
        while remaining:
            normalized = normalize_match_word(remaining[0])
            if normalized in {"the", "that", "a", "an"}:
                break
            candidate = name_words + [remaining[0]]
            if name_words and estimate_text_width(candidate) > MAX_EN_VISUAL_WIDTH:
                break
            name_words.append(remaining.pop(0))
        if name_words:
            chunks.append(name_words)

    return chunks, remaining


def chunk_english_for_subtitles(words: list[str], target_count: int) -> list[list[str]]:
    if target_count <= 0:
        return []
    if not words:
        return [[] for _ in range(target_count)]

    special_chunks, remaining_words = reserve_special_english_chunks(words)
    remaining_count = max(target_count - len(special_chunks), 0)
    if remaining_count <= 0:
        combined = special_chunks[:target_count]
    else:
        combined = special_chunks + chunk_words_into_count(remaining_words, remaining_count)

    fitted_chunks = []
    for chunk in combined:
        fitted_chunks.extend(split_oversized_chunk(chunk))

    while len(fitted_chunks) < target_count:
        fitted_chunks.append([])

    return fitted_chunks


def balanced_chunks(words: list[str], count: int, max_words_per_chunk: int = WORDS_PER_BLOCK) -> list[list[str]]:
    if count <= 0:
        return []
    if not words:
        return [[] for _ in range(count)]

    min_count = (len(words) + max_words_per_chunk - 1) // max_words_per_chunk
    count = min(max(count, min_count), len(words))
    remaining_words = len(words)
    remaining_chunks = count
    chunks = []
    index = 0

    while remaining_chunks:
        size = min(max_words_per_chunk, max(1, round(remaining_words / remaining_chunks)))
        if remaining_words - size < remaining_chunks - 1:
            size = remaining_words - (remaining_chunks - 1)
        chunks.append(words[index : index + size])
        index += size
        remaining_words -= size
        remaining_chunks -= 1

    return chunks


def chunk_spanish_for_english_alignment(words: list[str], en_chunks: list[list[str]]) -> list[list[str]]:
    if not words:
        return [[] for _ in en_chunks]
    if not en_chunks:
        return chunk_words(words)

    normalized_en = [[normalize_match_word(word) for word in chunk] for chunk in en_chunks]
    has_intro = (
        len(normalized_en) >= 3
        and normalized_en[0] == ["what", "if"]
        and normalized_en[1] == ["you", "had"]
    )

    if has_intro and len(words) >= 6:
        chunks = [words[:3], words[3:4]]
        name_size = min(max(len(en_chunks[2]), 1), 3, max(len(words) - 4, 1))
        chunks.append(words[4 : 4 + name_size])
        remaining_words = words[4 + name_size :]
        remaining_count = len(en_chunks) - len(chunks)
        chunks.extend(balanced_chunks(remaining_words, remaining_count))
    else:
        chunks = balanced_chunks(words, len(en_chunks))

    while len(chunks) < len(en_chunks):
        chunks.append([])
    return chunks


def build_intro_aligned_chunks(es_words: list[str], en_words: list[str]) -> tuple[list[list[str]], list[list[str]]] | None:
    special_en_chunks, remaining_en_words = reserve_special_english_chunks(en_words)
    if len(special_en_chunks) < 3 or len(es_words) < 6:
        return None

    name_size = min(max(len(special_en_chunks[2]), 1), 3, max(len(es_words) - 4, 1))
    es_chunks = [
        es_words[:3],
        es_words[3:4],
        es_words[4 : 4 + name_size],
    ]
    es_chunks.extend(chunk_words(es_words[4 + name_size :]))

    remaining_count = max(len(es_chunks) - len(special_en_chunks), 0)
    en_chunks = special_en_chunks + chunk_intro_remaining_english(remaining_en_words, remaining_count)
    if len(en_chunks) < len(es_chunks):
        en_chunks = expand_english_chunks_to_count(en_chunks, len(es_chunks))

    return es_chunks, en_chunks


def chunk_intro_remaining_english(words: list[str], count: int) -> list[list[str]]:
    if count <= 0:
        return []
    normalized = [normalize_match_word(word) for word in words]

    if count == 4 and normalized[:3] == ["the", "stand", "that"] and "before" in normalized:
        before_index = normalized.index("before")
        first = words[:3]
        second = words[3 : before_index + 1]
        rest = words[before_index + 1 :]

        if len(rest) >= 4 and [normalize_match_word(word) for word in rest[:3]] == ["you", "can", "even"]:
            return [first, second, rest[:3], rest[3:]]

    return chunk_words_into_count(words, count)


def split_chunk_once(words: list[str]) -> list[list[str]]:
    if len(words) <= 1:
        return [words]
    midpoint = max(1, len(words) // 2)
    return [words[:midpoint], words[midpoint:]]


def expand_english_chunks_to_count(en_chunks: list[list[str]], target_count: int) -> list[list[str]]:
    expanded = [list(chunk) for chunk in en_chunks]

    while len(expanded) < target_count:
        split_index = max(range(len(expanded)), key=lambda index: reading_weight(expanded[index]))
        pieces = split_chunk_once(expanded[split_index])
        if len(pieces) == 1:
            expanded.append([])
        else:
            expanded[split_index : split_index + 1] = pieces

    return expanded[:target_count]


def align_english_count_to_spanish(en_chunks: list[list[str]], target_count: int) -> list[list[str]]:
    if len(en_chunks) < target_count:
        return expand_english_chunks_to_count(en_chunks, target_count)

    if len(en_chunks) > target_count:
        return en_chunks[: target_count - 1] + [sum(en_chunks[target_count - 1 :], [])]

    return en_chunks


def fit_subtitle_chunks_to_video(
    es_chunks: list[list[str]],
    en_chunks: list[list[str]],
) -> tuple[list[list[str]], list[list[str]]]:
    while True:
        previous_counts = (len(es_chunks), len(en_chunks))
        es_chunks = fit_spanish_chunks_to_video(es_chunks)
        en_chunks = align_english_count_to_spanish(en_chunks, len(es_chunks))
        en_chunks = fit_english_chunks_to_video(en_chunks)

        if len(en_chunks) > len(es_chunks):
            es_chunks = balanced_chunks(sum(es_chunks, []), len(en_chunks))

        if previous_counts == (len(es_chunks), len(en_chunks)):
            return es_chunks, en_chunks


def align_paragraphs_to_count(paragraphs: list[str], count: int) -> list[str]:
    if count <= 0:
        return []
    if not paragraphs:
        return ["" for _ in range(count)]
    if len(paragraphs) == count:
        return paragraphs
    if len(paragraphs) > count:
        return paragraphs[: count - 1] + [" ".join(paragraphs[count - 1 :]).strip()]

    aligned = []
    total = len(paragraphs)
    for index in range(count):
        start = round(index * total / count)
        end = round((index + 1) * total / count)
        if end <= start:
            end = min(start + 1, total)
        aligned.append(" ".join(paragraphs[start:end]).strip())

    return aligned


def collect_timing_intervals(segments: list[dict] | None = None, blocks: list[dict] | None = None) -> list[tuple[float, float]]:
    source = segments if segments else blocks
    intervals = []

    for item in source or []:
        start = float(item.get("start", 0.0))
        end = float(item.get("end", start))
        if end > start:
            intervals.append((start, end))

    return intervals


def section_candidate_score(section_words: list[str], candidate_words: list[str]) -> float:
    if not section_words or not candidate_words:
        return 0.0

    section_set = set(section_words)
    candidate_set = set(candidate_words)
    overlap = len(section_set & candidate_set) / max(len(section_set), 1)
    count_fit = 1 - min(abs(len(candidate_words) - len(section_words)) / max(len(section_words), len(candidate_words), 1), 1)
    return (overlap * 0.7) + (count_fit * 0.3)


def distribute_segments_to_sections_by_text(
    sections: list[str],
    segments: list[dict],
) -> list[list[tuple[float, float]]]:
    if not sections:
        return []
    if not segments:
        return [[] for _ in sections]

    section_groups = []
    current_segment = 0

    for section_index, section in enumerate(sections):
        remaining_sections = len(sections) - section_index - 1
        if section_index == len(sections) - 1:
            group = segments[current_segment:]
            section_groups.append(collect_timing_intervals(segments=group))
            break

        max_end = max(current_segment + 1, len(segments) - remaining_sections)
        section_words = text_match_words(section)
        best_end = current_segment + 1
        best_score = -1.0
        candidate_words = []

        for end in range(current_segment + 1, max_end + 1):
            candidate_words.extend(text_match_words(segments[end - 1].get("text", "")))
            score = section_candidate_score(section_words, candidate_words)
            if score > best_score:
                best_score = score
                best_end = end

        group = segments[current_segment:best_end]
        section_groups.append(collect_timing_intervals(segments=group))
        current_segment = best_end

    while len(section_groups) < len(sections):
        section_groups.append([])

    return section_groups


def group_intervals_by_voice_gap(intervals: list[tuple[float, float]], gap_seconds: float = VOICE_GAP_SECONDS) -> list[list[tuple[float, float]]]:
    if not intervals:
        return []

    groups = [[intervals[0]]]
    for start, end in intervals[1:]:
        previous_end = groups[-1][-1][1]
        if start - previous_end > gap_seconds:
            groups.append([])
        groups[-1].append((start, end))

    return groups


def flatten_interval_groups(groups: list[list[tuple[float, float]]]) -> list[tuple[float, float]]:
    return [interval for group in groups for interval in group]


def distribute_intervals_to_sections(
    intervals: list[tuple[float, float]],
    section_weights: list[int],
) -> list[list[tuple[float, float]]]:
    if not section_weights:
        return []
    if not intervals:
        return [[] for _ in section_weights]

    groups = group_intervals_by_voice_gap(intervals)
    if len(groups) == len(section_weights):
        return groups

    weighted_total = sum(max(weight, 1) for weight in section_weights)
    total_duration = sum(end - start for start, end in intervals)
    current_time = intervals[0][0]
    sections = []

    for index, weight in enumerate(section_weights):
        if index == len(section_weights) - 1:
            sections.append([(current_time, intervals[-1][1])])
            break

        duration = total_duration * max(weight, 1) / weighted_total
        section_end = min(current_time + duration, intervals[-1][1])
        sections.append([(current_time, section_end)])
        current_time = section_end

    return sections


def time_at_progress(intervals: list[tuple[float, float]], progress: float, prefer_next_boundary: bool = False) -> float:
    remaining = max(progress, 0.0)

    for index, (start, end) in enumerate(intervals):
        duration = end - start
        is_last = index == len(intervals) - 1
        if remaining < duration or (remaining <= duration and (is_last or not prefer_next_boundary)):
            return start + remaining
        remaining -= duration

    return intervals[-1][1]


def distribute_times(intervals: list[tuple[float, float]], count: int) -> list[tuple[float, float]]:
    return distribute_times_by_weights(intervals, [1.0 for _ in range(count)])


def distribute_times_by_weights(intervals: list[tuple[float, float]], weights: list[float]) -> list[tuple[float, float]]:
    count = len(weights)
    if count <= 0:
        return []

    if not intervals:
        return [(round(index * 1.2, 2), round((index + 1) * 1.2, 2)) for index in range(count)]

    total_duration = sum(end - start for start, end in intervals)
    if total_duration <= 0:
        return [(round(index * 1.2, 2), round((index + 1) * 1.2, 2)) for index in range(count)]

    times = []
    total_weight = sum(max(weight, 0.25) for weight in weights)
    current_progress = 0.0

    for index in range(count):
        start_progress = current_progress
        current_progress += total_duration * max(weights[index], 0.25) / total_weight
        end_progress = current_progress if index < count - 1 else total_duration
        start = time_at_progress(intervals, start_progress, prefer_next_boundary=True)
        end = time_at_progress(intervals, end_progress)
        shifted_start = max(0.0, start - SUBTITLE_LEAD_SECONDS)
        shifted_end = max(shifted_start + 0.01, end - SUBTITLE_LEAD_SECONDS)
        times.append((round(shifted_start, 2), round(shifted_end, 2)))

    return times


def build_blocks_from_manual_text(
    text_es: str,
    text_en: str = "",
    segments: list[dict] | None = None,
    existing_blocks: list[dict] | None = None,
) -> list[dict]:
    es_paragraphs = split_text_paragraphs(text_es)
    if not es_paragraphs:
        return []

    en_paragraphs = align_paragraphs_to_count(split_text_paragraphs(text_en), len(es_paragraphs))
    section_weights = [len(split_text_words(paragraph)) for paragraph in es_paragraphs]

    if segments:
        section_intervals = distribute_segments_to_sections_by_text(es_paragraphs, segments)
    else:
        intervals = collect_timing_intervals(blocks=existing_blocks)
        section_intervals = distribute_intervals_to_sections(intervals, section_weights)

    blocks = []

    for paragraph_index, paragraph in enumerate(es_paragraphs):
        es_words = split_text_words(paragraph)
        en_words = split_text_words(en_paragraphs[paragraph_index])
        aligned_intro_chunks = build_intro_aligned_chunks(es_words, en_words)
        if aligned_intro_chunks:
            es_chunks, en_chunks = aligned_intro_chunks
        else:
            base_es_count = len(chunk_words(es_words))
            en_chunks = chunk_english_for_subtitles(en_words, base_es_count)
            es_chunks = chunk_spanish_for_english_alignment(es_words, en_chunks)

        es_chunks, en_chunks = fit_subtitle_chunks_to_video(es_chunks, en_chunks)
        block_weights = [
            max(reading_weight(es_chunks[index]), reading_weight(en_chunks[index]))
            for index in range(len(es_chunks))
        ]
        block_times = distribute_times_by_weights(section_intervals[paragraph_index], block_weights)

        for chunk_index, chunk in enumerate(es_chunks):
            start, end = block_times[chunk_index]
            text_es_block = " ".join(chunk).upper()
            text_en_block = " ".join(en_chunks[chunk_index]).upper() if chunk_index < len(en_chunks) else ""
            block = {
                "id": f"block_{len(blocks) + 1:03d}",
                "chain_index": paragraph_index + 1,
                "start": start,
                "end": end,
                "text_es": text_es_block,
                "text_en": text_en_block,
                "font_size_es": DEFAULT_FONT_SIZE_ES,
                "font_size_en": DEFAULT_FONT_SIZE_EN,
                "y_es": DEFAULT_Y_ES,
                "y_en": DEFAULT_Y_EN,
                "x": 540,
                "translation_warning": False,
                "translation_outdated": False,
            }
            block["words"] = build_words_for_block(text_es_block, start, end)
            blocks.append(block)

    return blocks


def build_blocks_from_segments(segments: list[dict], words_per_block: int = WORDS_PER_BLOCK) -> list[dict]:
    blocks = []

    for segment in segments:
        words = segment.get("text", "").split()
        if not words:
            continue

        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", start))
        duration = max(end - start, 0.01)
        seconds_per_word = duration / len(words)

        for index in range(0, len(words), words_per_block):
            chunk = words[index : index + words_per_block]
            block_start = start + (index * seconds_per_word)
            block_end = start + ((index + len(chunk)) * seconds_per_word)

            block = {
                    "id": f"block_{len(blocks) + 1:03d}",
                    "start": round(block_start, 2),
                    "end": round(block_end, 2),
                    "text_es": " ".join(chunk).upper(),
                    "text_en": "",
                    "font_size_es": DEFAULT_FONT_SIZE_ES,
                    "font_size_en": DEFAULT_FONT_SIZE_EN,
                    "y_es": DEFAULT_Y_ES,
                    "y_en": DEFAULT_Y_EN,
                    "x": 540,
                }
            block["words"] = build_words_for_block(block["text_es"], block["start"], block["end"])
            blocks.append(block)

    return blocks


def build_mock_blocks() -> list[dict]:
    return [
        {
            "id": "block_001",
            "start": 0.0,
            "end": 1.2,
            "text_es": "QUE PASARIA SI",
            "text_en": "WHAT WOULD HAPPEN IF",
            "font_size_es": 70,
            "font_size_en": 45,
            "y_es": 1500,
            "y_en": 1420,
            "x": 540,
        },
        {
            "id": "block_002",
            "start": 1.2,
            "end": 2.6,
            "text_es": "PUDIERAS EDITAR",
            "text_en": "YOU COULD EDIT",
            "font_size_es": 70,
            "font_size_en": 45,
            "y_es": 1500,
            "y_en": 1420,
            "x": 540,
        },
        {
            "id": "block_003",
            "start": 2.6,
            "end": 4.0,
            "text_es": "SUBTITULOS EN VIVO",
            "text_en": "LIVE SUBTITLES",
            "font_size_es": 70,
            "font_size_en": 45,
            "y_es": 1500,
            "y_en": 1420,
            "x": 540,
        },
    ]
