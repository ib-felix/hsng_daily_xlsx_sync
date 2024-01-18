import datetime
import functions as f

print(f"----- Running at UTC: {datetime.datetime.today().strftime('%Y-%m-%d %H:%M')} -----\n>>  START")

local_files_list, local_files_dict = f.listLocalImports()
remote_files_list, remote_files_dict = f.listRemoteImports()


if not f.checkForImportChanges(local_files_list, remote_files_list):
    print(f"<<  No changes detected, closing.")
    exit(0)

f.updateImports()

files_to_convert = f.getFilesToConvert(remote_files_dict)

if not files_to_convert:
    print(f'<<  The changes detected were deemed irrelevant, closing.')
    exit(0)

f.convertAndUploadFiles(files_to_convert,local_files_dict) 


print('<<  COMPLETE')