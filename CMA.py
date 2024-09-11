#Casey Donaldson
#2203162
#This application is to grab a file either image, docx and possibly video depending on the current stage.

#imports that will be used throughout the application
import argparse
#import pandas
import os #used for file paths

#imports for image metadata (JPEG)
import PIL
from PIL import Image, ExifTags
import piexif #used in modified data
from PIL.ExifTags import TAGS

#Used for geo locating
from geopy.geocoders import Nominatim
#from gmplot import gmplot, alternative
import folium

#used for reporting
import csv
from prettytable import PrettyTable


#My banner, lovely.
#https://patorjk.com/software/taag/#p=display&f=Soft&t=Casey's%0AFootprinting%0AScanner
print(r"""

    __        __   ___                                   
   /  `  /\  /__` |__  \ /                               
   \__, /~~\ .__/ |___  |                                
                                                         
                ___ ___       __       ___               
          |\/| |__   |   /\  |  \  /\   |   /\           
          |  | |___  |  /~~\ |__/ /~~\  |  /~~\          
                                                         
                                           __   ___  __  
                   /\  |\ |  /\  |    \ / /__` |__  |__) 
                  /~~\ | \| /~~\ |___  |  .__/ |___ |  \ 

                                                                                                       
    Please note this tool is for educational purposes
                                                                                    
""")

#out of use Todo
# def edit_metadata(filename, key, value):b nm,. 
#     try:
#         # Open the image file
#         image = Image.open(filename)
#         # Get the existing metadata
#         exif_dict = piexif.load(image.info["exif"])

#         # Iterate through data to find tag relating to key
#         for tag, tag_value in exif_dict.items():
#             print(f"tag - {tag}")
#             print(f"key - {key}")
#             if tag == key:
#                 exif_dict[tag] = value
#                 print(tag, tag_value)
#                 break

#         # Save the image with updated metadata
#         exif_bytes = piexif.dump(exif_dict)
#         image.save(filename, exif=exif_bytes)

#         print("Metadata updated")

#     except Exception as x:
#         print(f"Error: {x}")

        

#function to exstract meta data from a jpg file
def image_metadata_exstractor(filename, delete_metadata, modify_metadata_key=None, modify_metadata_value=None):

    try:
        #open the image and save as varible
        file = open(filename, "rb")
        image = Image.open(file)

    #exceptions that might cause a crash
    except FileNotFoundError:
        print(f"File not found - {filename}")
        return
    except PIL.UnidentifiedImageError as e:
        print(f"Error: Unable to identify image file - {filename}")
        return
    except Exception as x:
        print(f"Error - {x}")
        return #exit incase of error
 
    #get exif data for further analysis
    exifdata = image.getexif()

    #check data is not null
    if exifdata is not None:

        #if delete data flag is raised
        if delete_metadata == True:
            #alert deleting data
            print("Deleting metadata...")
            try:
                # Remove exif data from the image
                image.info["exif"] = b""
                # Save the image with no data
                image.save(filename)    
                print("Metadata deleted successfully.")
                return
                
            except Exception as e:
                print(f"Error deleting metadata: {e}")

        #if modified data raised then perform this
        if modify_metadata_key and modify_metadata_value:
            print("Modification is not implemented currently")
            #edit_metadata(filename, modify_metadata_key, modify_metadata_value)
        
        #grab basic information on most images
        info_dict = {
            "Image Size": image.size,
            "Image Height": image.height,
            "Image Width": image.width,
            "Image Format": image.format,
            "Image Mode": image.mode,
            "Image is Animated": getattr(image, "is_animated", False),
            "Frames in Image": getattr(image, "n_frames", 1)
        }

        #go through each tag and value
        for tag_id in exifdata:
            tag = TAGS.get(tag_id, tag_id)
            data = exifdata.get(tag_id)

            #if there add to dict
            if isinstance(data, bytes):
                data = data.decode()
            
            #updating dict
            info_dict.update({tag : data})

        #create a table 
        table = PrettyTable()
        #add feild names
        table.field_names = ["Key", "Value"]

        #iterate through the dict
        for key, value in info_dict.items():
            #add each key value to table
            table.add_row([key, value])
        
        #print the table to the terminal
        print(table.get_string())
            
        #if output is wanted
        if output_metadata == True:
            print("Outputting")
            #this is used to report to a csv file
            dict_to_csv(info_dict, csv_file=output_file)
            

            #attemp geo data as well
            if 'GPSInfo' in info_dict:
                image_locator(filename=filename)
    else:
        print("Unable to read any exif data.")



#fuction to get location of data if possible
def image_locator(filename):
    try:
        #re-open image
        img = Image.open(filename)

        #collect metadata and tags
        exifdata = {
            ExifTags.TAGS[key]: value
            for key, value in img._getexif().items()
            #check key/tags
            if key in ExifTags.TAGS
        }
       
        # Check if GPSInfo is present
        if 'GPSInfo' not in exifdata:
            raise ValueError("GPS information not found")

        #declare that inside GPSinfo 2nd field is the north coordinates
        north = exifdata['GPSInfo'][2]
        #declare that inside GPSinfo 4th field is the east coordinates
        east = exifdata["GPSInfo"][4]

        #reform the format of the coordinates to lat and lng for processing
        lat = ((((north[0] * 60) + north[1]) * 60) + north[2]) / 60 / 60
        lng = ((((east[0] * 60) + east[1]) * 60) + east[2]) / 60 / 60

        #Check if the value is positive or negative. north or south ect.
        if exifdata.get('GPSInfo')[1] == 'S':
            lat = -lat
        if exifdata.get('GPSInfo')[3] == 'W':
            lng = -lng

        #print(lat, lng)

        #change from fraction to floating points
        lat, lng = float(lat), float(lng)

        #check lat and long
        #print(lat, lng)

        #folium use create a instance of the map with the lat and lng including current zoom
        fmap = folium.Map(location=[lat, lng], zoom_start=12)
        #add marker to map
        folium.Marker(location=[lat,lng], popup='Location', icon=folium.Icon(color='blue')).add_to(fmap)
        #save the map
        fmap.save(f'{filename} - Map.html')
        print("map saved")

    except Exception as e:
        if delete_metadata == True:
            print("Data correctly deleted")
        else:
            print(f"Error exception: {e}")
            print("No Geo Data")


#dictionary to csv file function
def dict_to_csv(dict, csv_file):

    print(f"Output file path: {output_file}")
    #print(csv_file_path)
    #open new csv file
    with open(csv_file, 'w', newline='') as csvfile:
        
        #define the writter
        csv_writer = csv.writer(csvfile)

        #write the headers
        csv_writer.writerow(["Metadata Key", "Metadata Value"])
        
        #iterate through the dict
        for key, value in dict.items():
    
            #Go through each key value pair and format the key and value before writting to the csv file
            formatted_key = f"{key.strip()}"
            formatted_value = f"{str(value).strip()}"

            #write the CSV file
            csvfile.write(f"{formatted_key:25}, {formatted_value}\n")
         
        
#function to find what file is given
def get_file_ex(filename):

    #Split the file name and grab the exstention
    file_ex = filename.split('.')

    #file exstention exsists
    if len(file_ex) > 1:
        #grab the exstention
        ex = file_ex[-1].lower() #convert to lower case

        #check exstention and use an elif statement to direct to the correct function for analysis
        if ex =="txt": print("Text files contain no metadata")
        elif ex == "jpg" or ex == "jpeg": 
            print(f"Trying to access image {filename}")
            image_metadata_exstractor(filename=filename, delete_metadata=delete_metadata,
            modify_metadata_key=modify_metadata_key, modify_metadata_value=modify_metadata_value)
        elif ex == "png" or ex == "PNG": print("png")
        elif ex == "pdf": print("PDF file")
        else:
            print("Unknown file type")

        #other file types to be implemented




#This is used to ensure the application is useable for new people by giving advice and help options
parser = argparse.ArgumentParser("" , formatter_class=argparse.RawTextHelpFormatter)

group = parser.add_mutually_exclusive_group(required=True)
# Required arguments
group.add_argument("--file", help="The file path to the file to be analyzed, example: Desktop/image.png", required=False)
# Required arguments
group.add_argument("--folder", help="The file path to the folder to be analyzed, example: Desktop/folder", required=False)


# Optional args
parser.add_argument("-d", "--delete", help="WARNING ONLY: Use this flag to initiate the deletion metadata", action='store_true')
parser.add_argument("-o", "--output", help="Use this flag to output results to a csv file and create a map, if applicable", action='store_true')
parser.add_argument("-m", "--modify", nargs=2, metavar=('key', 'value'), help=
'''Modify metadata with the specified key and value
Example: python your_script.py image.jpg -m Software ModifiedSoftware 
''')


#Now parse them.
args = parser.parse_args()

#Define variables.
File=str(args.file)
Folder=str(args.folder)
modify_metadata = args.modify
delete_metadata = args.delete
output_metadata = args.output

#if modify flag provided with both values raise function else define values as NONE
modify_metadata_key, modify_metadata_value = modify_metadata if modify_metadata else (None, None)


#if file provided
if args.file:

    #Print them out.
    print ("The File specified is", File)

    #create vari for file
    stage = args.file

    #create output file
    output_file = os.path.join(os.path.dirname(stage), f"{os.path.splitext(os.path.basename(stage))[0]}_File_output.csv")

    #execute on file only
    get_file_ex(filename=File)

elif args.folder:

    #Print them out.
    print ("The Folder specified is", Folder)

    #iterate through the folder
    for fileimage in os.listdir(Folder):
        
        #define vari for each image
        stage = os.path.abspath(os.path.join(Folder, fileimage))
        print(f"stage: {stage}")

        #define output file
        output_file = os.path.join(os.path.dirname(stage), f"{os.path.splitext(os.path.basename(stage))[0]}_File_output.csv")# os.path.join(fileimage, "Folder_output.csv")
   
        get_file_ex(filename=stage)

else:
    print("Please provide either --file or --folder.")
    output_file = None

#Todo
#modify function