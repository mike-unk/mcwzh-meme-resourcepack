import zipfile
import json
import argparse
import os
import sys
import hashlib

# Lincese: Apache-2.0


def main():
    args = vars(generate_parser().parse_args())
    if args['type'] == 'clean':
        for i in os.listdir('builds/'):
            os.remove(os.path.join('builds', i))
        print("\nDeleted all packs built.")
    else:
        pack_builder = builder()
        pack_builder.args = args
        pack_builder.build()


class builder(object):
    '''Build packs.'''

    def __init__(self):
        self.__args = {}
        self.__warning = 0
        self.__error = 0
        self.__logs = ""
        self.__filename = ""

    @property
    def args(self):
        return self.__args

    @args.setter
    def args(self, value: dict):
        self.__args = value

    @property
    def warning_count(self):
        return self.__warning

    @property
    def error_count(self):
        return self.__error

    @property
    def filename(self):
        return self.__filename != "" and self.__filename or "Did not build any pack."

    @property
    def logs(self):
        return self.__logs != "" and self.__logs or "Did not build any pack."

    def clean_status(self):
        self.__warning = 0
        self.__error = 0
        self.__logs = ""
        self.__filename = ""

    def build(self):
        self.clean_status()
        args = self.args
        # checking module names first, preventing name conflict
        checker = module_checker()
        if checker.check_module():
            # process args
            # get language supplement
            lang_supp = self.__parse_includes(
                args['language'], checker.language_module_list)
            # merge sfw into lang_supp
            if args['sfw'] and 'sfw' not in lang_supp:
                lang_supp.append('sfw')
            # get resource supplement
            res_supp = self.__parse_includes(
                args['resource'], checker.resource_module_list)
            # get mods strings
            mod_supp = self.__parse_mods(args['mod'])
            # merge language supplement
            # TODO: split mod strings into namespaces
            main_lang_data = self.__merge_language(lang_supp, mod_supp)
            # get realms strings
            realms_lang_data = json.load(open(os.path.join(os.path.dirname(
                __file__), "assets/realms/lang/zh_meme.json"), 'r', encoding='utf8'))
            # process pack name
            digest = hashlib.sha256(json.dumps(
                args).encode('utf8')).hexdigest()
            pack_name = args['hash'] and f"mcwzh-meme.{digest[:7]}.zip" or "mcwzh-meme.zip"
            self.__filename = pack_name
            # process mcmeta
            mcmeta = self.__process_meta(args['type'])
            # decide language file name & ext
            lang_file_name = self.__get_lang_file_name(args['type'])
            # create pack
            info = f"Building pack {pack_name}"
            print(info)
            self.__logs += f"{info}\n"
            # set output dir
            output_dir = 'output' in args and args['output'] or 'builds'
            pack_name = os.path.join(output_dir, pack_name)
            # mkdir
            if os.path.exists(output_dir) and not os.path.isdir(output_dir):
                os.remove(output_dir)
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)
            # create pack
            pack = zipfile.ZipFile(
                pack_name, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=5)
            pack.write(os.path.join(os.path.dirname(
                __file__), "pack.png"), arcname="pack.png")
            pack.write(os.path.join(os.path.dirname(
                __file__), "LICENSE"), arcname="LICENSE")
            pack.writestr("pack.mcmeta", json.dumps(
                mcmeta, indent=4, ensure_ascii=False))
            # dump lang file into pack
            if args['type'] != 'legacy':
                # normal/compat
                pack.writestr(f"assets/minecraft/lang/{lang_file_name}",
                              json.dumps(main_lang_data, indent=4, ensure_ascii=True))
                pack.writestr(f"assets/realms/lang/{lang_file_name}",
                              json.dumps(realms_lang_data, indent=4, ensure_ascii=True))
            else:
                # legacy
                main_lang_data.update(realms_lang_data)
                legacy_content = self.__generate_legacy_content(main_lang_data)
                pack.writestr(
                    f"assets/minecraft/lang/{lang_file_name}", legacy_content)
            # dump resources
            self.__dump_resources(res_supp, pack)
            pack.close()
            print("Build successful.")
        else:
            error = "Error: " + checker.info
            print(f"\033[1;31m{error}\033[0m", file=sys.stderr)
            self.__logs += f"{error}\n"
            self.__error += 1
            print(
                "\033[1;31mTerminate building because an error occurred.\033[0m")

    def __dump_resources(self, modules: list, pack: zipfile.ZipFile):
        for item in modules:
            base_folder = os.path.join(
                os.path.dirname(__file__), "modules", item)
            for root, dirs, files in os.walk(base_folder):
                for file in files:
                    if file != "manifest.json":
                        path = os.path.join(root, file)
                        arcpath = path[path.find(
                            base_folder) + len(base_folder) + 1:]
                        testpath = arcpath.replace(os.sep, "/")
                        # prevent duplicates
                        if testpath not in pack.namelist():
                            pack.write(os.path.join(
                                root, file), arcname=arcpath)
                        else:
                            warning = f"Warning: Duplicated '{testpath}', skipping."
                            print(
                                f"\033[33m{warning}\033[0m", file=sys.stderr)
                            self.__logs += f"{warning}\n"
                            self.__warning += 1

    def __process_meta(self, type: str) -> dict:
        data = json.load(open(os.path.join(os.path.dirname(
            __file__), 'pack.mcmeta'), 'r', encoding='utf8'))
        if type == 'compat':
            data.pop('language')
        elif type == 'legacy':
            data['pack']['pack_format'] = 3
        return data

    def __get_lang_file_name(self, type: str):
        return type == 'normal' and 'zh_meme.json' or (type == 'compat' and 'zh_cn.json' or 'zh_cn.lang')

    def __parse_includes(self, includes: list, fulllist: list) -> list:
        if 'none' in includes:
            return []
        elif 'all' in includes:
            return fulllist
        else:
            include_list = []
            for item in includes:
                if item in fulllist:
                    include_list.append(item)
                elif os.path.exists(os.path.normpath(item)) and self.__convert_path_to_module(
                        os.path.normpath(item)) in fulllist:
                    include_list.append(self.__convert_path_to_module(
                        os.path.normpath(item)))
                else:
                    warning = f"Warning: '{item}' does not exist, skipping."
                    print(f"\033[33m{warning}\033[0m", file=sys.stderr)
                    self.__logs += f"{warning}\n"
                    self.__warning += 1
            return include_list

    def __convert_path_to_module(self, path: str) -> str:
        return json.load(open(os.path.join(path, "manifest.json"), 'r', encoding='utf8'))['name']

    def __parse_mods(self, mods: list) -> list:
        existing_mods = os.listdir(os.path.join(
            os.path.dirname(__file__), 'mods'))
        if 'none' in mods:
            return []
        elif 'all' in mods:
            return existing_mods
        else:
            mods_list = []
            for item in mods:
                if item in existing_mods:
                    mods_list.append(item)
                elif os.path.basename(os.path.normpath(item)) in existing_mods:
                    mods_list.append(os.path.basename(os.path.normpath(item)))
                else:
                    warning = f"Warning: '{item}' does not exist, skipping."
                    print(f"\033[33m{warning}\033[0m", file=sys.stderr)
                    self.__logs += f"{warning}\n"
                    self.__warning += 1
            return mods_list

    def __merge_language(self, language_supp: list, mod_supp: list) -> dict:
        # load basic strings
        lang_data = json.load(open(os.path.join(os.path.dirname(
            __file__), "assets/minecraft/lang/zh_meme.json"), 'r', encoding='utf8'))
        for item in language_supp:
            add_file = os.path.join("modules", item, "add.json")
            remove_file = os.path.join("modules", item, "remove.json")
            if os.path.exists(add_file):
                lang_data.update(
                    json.load(open(add_file, 'r', encoding='utf8')))
            if os.path.exists(remove_file):
                for key in json.load(open(remove_file, 'r', encoding='utf8')):
                    if key in lang_data:
                        lang_data.pop(key)
                    else:
                        warning = f"Warning: Key '{key}' does not exist, skipping."
                        print(f"\033[33m{warning}\033[0m", file=sys.stderr)
                        self.__logs += f"{warning}\n"
                        self.__warning += 1
        lang_data.update(self.__get_mod_content(mod_supp))
        return lang_data

    def __get_mod_content(self, mod_list: list) -> dict:
        mods = {}
        for file in mod_list:
            if file.endswith(".json"):
                mods.update(json.load(open(os.path.join(os.path.dirname(
                    __file__), "mods", file), 'r', encoding='utf8')))
            elif file.endswith(".lang"):
                with open(os.path.join(os.path.dirname(__file__), "mods", file), 'r', encoding='utf8') as f:
                    mods.update(line.strip().split(
                        "=", 1) for line in f if line.strip() != '' and not line.startswith('#'))
            else:
                warning = f'Warning: File type "{file[file.rfind(".") + 1:]}" is not supported, skipping.'
                print(
                    f'\033[33m{warning}\033[0m', file=sys.stderr)
                self.__warning += 1
                self.__logs += f"{warning}\n"
        return mods

    def __generate_legacy_content(self, content: dict) -> str:
        # get mappings list
        mappings = json.load(open(os.path.join(
            "mappings", "all_mappings"), 'r', encoding='utf8'))['mappings']
        legacy_lang_data = {}
        for item in mappings:
            mapping_file = item + ".json"
            if mapping_file not in os.listdir("mappings"):
                warning = f"Warning: Missing mapping '{mapping_file}', skipping."
                print(f"\033[33m{warning}\033[0m", file=sys.stderr)
                self.__logs += f"{warning}\n"
                self.__warning += 1
            else:
                mapping = json.load(
                    open(os.path.join("mappings", mapping_file), 'r', encoding='utf8'))
                for k, v in mapping.items():
                    if v not in content:
                        warning = f"Warning: Corrupted key-value pair in file {mapping_file}: {{'{k}': '{v}'}}, skipping."
                        print(
                            f"\033[33m{warning}\033[0m", file=sys.stderr)
                        self.__logs += f"{warning}\n"
                        self.__warning += 1
                    else:
                        legacy_lang_data[k] = content[v]
        out_content = ""
        for k, v in legacy_lang_data.items():
            out_content += f"{k}={v}\n"
        return out_content


class module_checker(object):
    def __init__(self):
        self.__status = True
        self.__checked = False
        self.__lang_list = []
        self.__res_list = []
        self.__manifests = {}
        self.__info = ''

    @property
    def info(self):
        return self.__info

    @property
    def language_module_list(self):
        if not self.__checked:
            self.check_module()
        return self.__status and self.__lang_list or []

    @property
    def resource_module_list(self):
        if not self.__checked:
            self.check_module()
        return self.__status and self.__res_list or []

    @property
    def manifests(self):
        if not self.__checked:
            self.check_module()
        return self.__status and self.__manifests or {}

    def clean_status(self):
        self.__status = True
        self.__checked = False
        self.__lang_list = []
        self.__res_list = []
        self.__manifests = {}
        self.__info = ''

    def check_module(self):
        self.clean_status()
        base_folder = os.path.join(os.path.dirname(__file__), 'modules')
        lang_list = []
        res_list = []
        for module in os.listdir(base_folder):
            manifest = os.path.join(base_folder, module, "manifest.json")
            if os.path.exists(manifest) and os.path.isfile(manifest):
                data = json.load(open(manifest, 'r', encoding='utf8'))
                name = data['name']
                module_type = data['type']
                if name in lang_list or name in res_list:
                    self.__checked = True
                    self.__status = False
                    self.__info = f"Conflict name '{name}'."
                    return False
                else:
                    self.__manifests[name] = data['description']
                    if module_type == 'language':
                        lang_list.append(name)
                    elif module_type == 'resource':
                        res_list.append(name)
            else:
                self.__checked = True
                self.__status = False
                self.__info = f"Bad module '{module}', no manifest file."
                return False
        self.__status = True
        self.__checked = True
        self.__lang_list = lang_list
        self.__res_list = res_list
        return True


def generate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Automatically build resourcepacks")
    parser.add_argument('type', default='normal', choices=[
                        'normal', 'compat', 'legacy', 'clean'], help="Build type. Should be 'normal', 'compat', 'legacy' or 'clean'. If it's 'clean', all packs in 'builds/' directory will be deleted.")
    parser.add_argument('-r', '--resource', nargs='*', default='all',
                        help="(Experimental) Include resource modules. Should be module names, 'all' or 'none'. Defaults to 'all'. Pseudoly accepts a path, but only module paths in 'modules' work.")
    parser.add_argument('-l', '--language', nargs='*', default='none',
                        help="(Experimental) Include language modules. Should be module names, 'all' or 'none'. Defaults to 'none'. Pseudoly accepts a path, but only module paths in 'modules' work.")
    parser.add_argument('-s', '--sfw', action='store_true',
                        help="Use 'suitable for work' strings, equals to '--language sfw'.")
    parser.add_argument('-m', '--mod', nargs='*', default='none',
                        help="(Experimental) Include mod string files. Should be file names in 'mods/' folder, 'all' or 'none'. Defaults to 'none'. Pseudoly accepts a path, but only files in 'mods/' work.")
    parser.add_argument(
        '-o', '--output', help="Specify the location to output packs. Default location is 'builds/' folder.")
    parser.add_argument('--hash', action='store_true',
                        help="Add a hash into file name.")
    return parser


if __name__ == "__main__":
    main()
