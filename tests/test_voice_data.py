from app.voice_data import NumericChoices, VoiceMetadata, parse_voice_config


def test_parse_voice_config_with_named_speakers():
    config = {
        "speaker_id_map": {"alice": 0, "bob": 1},
        "inference": {
            "length_scale": 1.0,
            "noise_scale": 0.667,
            "noise_w": 0.333,
        },
    }

    metadata: VoiceMetadata = parse_voice_config("pt_test", config)

    assert metadata.speaker_choices == {"alice": 0, "bob": 1}
    assert metadata.default_speaker == "alice"

    length_scale: NumericChoices = metadata.numeric_parameters["length_scale"]
    assert length_scale.default_label in length_scale.values
    assert length_scale.values[length_scale.default_label] == 1.0
    assert any(value != 1.0 for value in length_scale.values.values())


def test_parse_voice_config_with_speaker_count():
    config = {
        "num_speakers": 3,
        "inference": {"length_scale": 1.2},
    }

    metadata = parse_voice_config("multi", config)

    assert metadata.speaker_choices == {
        "Speaker 0": 0,
        "Speaker 1": 1,
        "Speaker 2": 2,
    }
    assert metadata.default_speaker == "Speaker 0"


def test_parse_voice_config_without_optional_parameters():
    config = {}

    metadata = parse_voice_config("simple", config)

    assert metadata.speaker_choices == {}
    assert metadata.numeric_parameters == {}
