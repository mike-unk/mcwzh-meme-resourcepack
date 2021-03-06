import build
import os


def main():
    preset_args = [
        {'type': 'normal', 'language': [], 'resource': [
            'all'], 'mod': ['all'], 'sfw': True, 'hash': False, 'output': None},
        {'type': 'normal', 'language': [], 'resource': [
            'all'], 'mod': [], 'sfw': True, 'hash': False, 'output': None},
        {'type': 'normal', 'language': [], 'resource': [
        ], 'mod': [], 'sfw': True, 'hash': False, 'output': None},
        {'type': 'compat', 'language': [], 'resource': [
            'all'], 'mod': ['all'], 'sfw': True, 'hash': False, 'output': None},
        {'type': 'compat', 'language': [], 'resource': [
            'all'], 'mod': [], 'sfw': True, 'hash': False, 'output': None},
        {'type': 'compat', 'language': [], 'resource': [
        ], 'mod': [], 'sfw': True, 'hash': False, 'output': None},
        {'type': 'legacy', 'language': ['attributes', 'old_strings', 'diamond_hoe'], 'resource': [
        ], 'mod': [], 'sfw': True, 'hash': False, 'output': None},
        {'type': 'normal', 'language': [], 'resource': [
            'all'], 'mod': ['all'], 'sfw': False, 'hash': False, 'output': None},
    ]
    preset_name = [
        "mcwzh-meme_sfw.zip",
        "mcwzh-meme_nomod_sfw.zip",
        "mcwzh-meme_nomod_noresource_sfw.zip",
        "mcwzh-meme_compatible_sfw.zip",
        "mcwzh-meme_compatible_nomod_sfw.zip",
        "mcwzh-meme_compatible_nomod_noresource_sfw.zip",
        "mcwzh-meme_legacy_noresource_sfw.zip",
        "mcwzh-meme.zip"
    ]
    pack_builder = build.builder()
    pack_counter = 0
    perfect_pack_counter = 0
    base_folder = "builds"
    if os.path.exists(base_folder) and not os.path.isdir(base_folder):
        os.remove(base_folder)
    if not os.path.exists(base_folder):
        os.mkdir(base_folder)
    for file in os.listdir(base_folder):
        os.remove(os.path.join(base_folder, file))
    for item, name in zip(preset_args, preset_name):
        pack_builder.args = item
        pack_builder.build()
        if pack_builder.error_count == 0:
            pack_counter += 1
            if pack_builder.warning_count == 0:
                perfect_pack_counter += 1
            if name != "mcwzh-meme.zip":
                os.rename("builds/mcwzh-meme.zip",
                          os.path.join(base_folder, name))
            print(f"Renamed pack to {name}.")
        else:
            print(f"Failed to build pack {name}.")
    print(
        f"Built {pack_counter} packs with {perfect_pack_counter} pack(s) no warning.")


if __name__ == "__main__":
    main()
