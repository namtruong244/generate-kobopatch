import os
import requests
import shutil
import yaml
from zipfile import ZipFile
from tqdm.auto import tqdm
import subprocess


KOBO_UPDATE_FILE_NAME = 'kobo-update-'
KOBO_PATCH_URL = 'pgaskin/kobopatch-patches'


def main():
    for filename in os.listdir():
        file = os.path.join(filename)
        # checking if it is a file
        if os.path.isfile(file) and KOBO_UPDATE_FILE_NAME in file:
            update_version = file[len(KOBO_UPDATE_FILE_NAME):-4]

            print('Downloading KoboPatch for version', update_version)
            response = requests.get(f'https://api.github.com/repos/{KOBO_PATCH_URL}/releases/latest')
            latest_release_version = response.json()['name']

            # make an HTTP request within a context manager
            with requests.get(f'https://github.com/{KOBO_PATCH_URL}/releases/download/{latest_release_version}/kobopatch_{update_version}.zip', stream=True) as r:
                if not r.ok:
                    print(f'Version {update_version} is invalid or kobopatch for version {update_version} is not available. Please check version and try again later!')
                    exit()

                # check header to get content length, in bytes
                total_length = int(r.headers.get('Content-Length'))

                # implement progress bar via tqdm
                with tqdm.wrapattr(r.raw, 'read', total=total_length, desc='') as raw:
                    # save the output to a file
                    content_disposition = r.headers['Content-Disposition']
                    kobo_patch_file_name = content_disposition[content_disposition.find('filename') + len('filename') + 1:]

                    with open(kobo_patch_file_name, 'wb') as output:
                        shutil.copyfileobj(raw, output)

                print(f'Downloaded {kobo_patch_file_name}')

            kobo_patch_folder = f'./{kobo_patch_file_name[:-4]}'
            shutil.rmtree(kobo_patch_folder, ignore_errors=True)
            # loading the zip file and creating a zip object
            with ZipFile(f'./{kobo_patch_file_name}', 'r') as zObject:
                # Extracting all the members of the zip
                zObject.extractall(path=kobo_patch_folder)

            os.remove(kobo_patch_file_name)
            shutil.copy(filename, f'{kobo_patch_folder}/src/')
            shutil.copytree('./input/fonts/', f'{kobo_patch_folder}/src/fonts/', dirs_exist_ok=True)

            kobopatch_file = parse_yaml(f'{kobo_patch_folder}/kobopatch.yaml')
            config_file = parse_yaml('./input/config.yaml')
            for config_name, value_patch in config_file.items():
                kobopatch_file[config_name] = value_patch

            with open(rf'{kobo_patch_folder}/kobopatch.yaml', 'w') as file:
                yaml.dump(kobopatch_file, file)

            for file in os.listdir(f'{kobo_patch_folder}/bin/'):
                os.system(f'chmod +x {kobo_patch_folder}/bin/{file}')

            run_batch = f'{kobo_patch_folder}/kobopatch.bat' if os.name == 'nt' else f'sh {kobo_patch_folder}/kobopatch.sh'
            subprocess.call(run_batch.split(' '))

            shutil.copytree(f'{kobo_patch_folder}/out', './result', dirs_exist_ok=True)
            shutil.rmtree(f'{kobo_patch_folder}')
            print('Done')


def parse_yaml(path):
    with open(path, encoding='utf-8') as f:
        return yaml.full_load(f)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
