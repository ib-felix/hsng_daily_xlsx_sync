import subprocess
import requests
import pandas
import json
import os

path_here = '/home/felix/customer/hsng/hsng_daily_xlsx_sync'
cli = '/home/felix/sift-cli/cli_autoauth'

def updateImports():
    if(os.path.isdir(f'{path_here}/imports')):
        if(os.listdir(f'{path_here}/imports')):
            subprocess.run(f'rm {path_here}/imports/*', shell=True)
        subprocess.run(f'rmdir {path_here}/imports', shell=True)
    commands = [
        cli,
        'hsng.infobaleen.com',
        'download-dir',
        '-src', '/files/imports',
        '-target', f'{path_here}/imports'
    ]
    subprocess.run(commands)



def listLocalImports():
    files_list = []
    for file in os.listdir(f'{path_here}/imports'):
        files_list.append({
            "Filename": file, 
            "Modified": int(os.path.getmtime(f'{path_here}/imports/{file}'))
        })
    files_list.sort(key = lambda file : file['Filename'])
    files_dict = {}
    [files_dict.update({file["Filename"]: file["Modified"]}) for file in files_list]
    return files_list, files_dict

def listRemoteImports():
    commands = [
        cli,
        'hsng.infobaleen.com',
        'list-files'
    ]
    resp = subprocess.run(commands,capture_output=True)

    import_dir = '/files/imports/'
    files_list = []
    for row in resp.stdout.decode('utf-8').splitlines()[1:]:
        data = json.loads(row)
        if bool(data["IsDir"]) or import_dir not in data["Path"]:
            continue
        files_list.append({
            "Filename": data["Path"].replace(import_dir,''), 
            "Modified": int(data["Modified"])
        })
    files_list.sort(key = lambda file : file['Filename'])
    files_dict = {}
    [files_dict.update({file["Filename"]: file["Modified"]}) for file in files_list]
    return files_list, files_dict


def checkForImportChanges(local_files: list, remote_files: list):
    print_prefix = ' >> Updating local imports:'
    if len(local_files) != len(remote_files):
        print(f'{print_prefix} Difference in number of local and remote files')
        return True
    for (local_file, remote_file) in zip(local_files, remote_files):
        if local_file["Filename"] != remote_file["Filename"]:
            print(f'{print_prefix} Local file {local_file["Filename"]} missmatch to remote file {remote_file["Filename"]}')
            return True
        if local_file["Modified"] < remote_file["Modified"]:
            print(f'{print_prefix} Detected more recent changes to remote version of file {remote_file["Filename"]}')
            return True
    return False

    
def getFilesToConvert(remote_files: dict):
    files_to_convert = []
    for source_file in [file for file in remote_files.keys() if ".xlsx" in file]:
        converted_file = str(source_file).replace('.xlsx','.csv')
        if converted_file in remote_files.keys() and remote_files[converted_file] > remote_files[source_file]:
            print(f" >> {source_file} has a newer csv conversion")
            continue
        files_to_convert.append(source_file)
    return files_to_convert



def convertAndUploadFiles(files_to_convert:list, local_files:dict):
    for source_file in files_to_convert:
        converted_file = str(source_file).replace('.xlsx','.csv')
        if(converted_file in local_files.keys()):
            subprocess.run(['rm',f'{path_here}/imports/{converted_file}'])
            deleteRemoteFile(converted_file)
        print(f" >> Creating and uploading {converted_file}...")
        uploadFile(convertExcelToCSV(source_file))


def convertExcelToCSV(filename):
    file_path = f'{path_here}/imports/{filename}'
    if not os.path.isfile(file_path):
        print(f' (!) Error: {filename} not found in {path_here}/imports')
        return ''
    pandas.read_excel(file_path).to_csv(file_path.replace('.xlsx','.csv'), index=None, header=True)
    return filename.replace('.xlsx','.csv')

def uploadFile(local_file, target_file = None):
    if not target_file:
        target_file = local_file
    commands = [
        cli,
        'hsng.infobaleen.com',
        'upload-file',
        '-src', f'{path_here}/imports/{local_file}',
        '-dest', target_file
    ]
    subprocess.run(commands)

def deleteRemoteFile(filename):
    with open(path_here+'/.sift_key') as keyfile:
        sift_key=keyfile.readline()
    delete_path = f"https://hsng.infobaleen.com/api/v1/files/delete?path={filename}"    
    requests.get(delete_path, headers={'Authorization': sift_key})
