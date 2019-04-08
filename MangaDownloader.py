import requests, bs4, time, os, getpass, re


### functions for creating folders ###


#creates a parent folder containing manga subfolders
def create_parent_folder(manga):
    parent_folder = f"C:\\Users\\{getpass.getuser()}\\Desktop\\Downloaded Manga"    #creates a 'Downloaded Manga' folder on the user's Desktop
    os.makedirs(parent_folder, exist_ok=True)
    folder_title = re.sub(r'[\\/*?:%."<>|]', " ", manga)    #replaces invalid characters for folder names with a space
    manga_folder = f"{parent_folder}\\{folder_title}"   #creates a <manga title> folder in the 'Downloaded Manga' folder
    os.makedirs(manga_folder, exist_ok=True)
    return manga_folder

#creates chapter subfolders containing manga pages (in the manga subfolders)
def create_subfolder(folder, url):
    reversed_url = url[::-1]
    index = reversed_url.index("_")
    chapter_num = url[-index:]  #gets the chapter number (it's a hassle because some chapter numbers contain decimal points/alphabets)
    subfolder_title = create_subfolder_name(chapter_num)
    chapter_subfolder = f"{folder}\\Chapter {subfolder_title}"  #creates a <chapter number> folder in the <manga title> folder
    return chapter_subfolder

#add 0s to the chapter folder names where appropriate (otherwise, e.g. Chapter 1 and 100 will be incorrectly side by side)
def create_subfolder_name(chapter_str):
    rounded_str = str(round(float(chapter_str)//1))     
    if len(rounded_str) == 1:
        return "00" + chapter_str
    elif len(rounded_str) == 2:
        return "0" + chapter_str
    else:
        return chapter_str

### functions related to processing URLs ###

        
#returns the HTML source code of any webpage
def get_source_code(url):
    res = requests.get(url)
    res.raise_for_status
    return bs4.BeautifulSoup(res.text, "html.parser")

#returns a list of URLs to all manga pages from a single chapter
def get_image_links(url, website):
    chapter_code = get_source_code(url)
    if website == "MangaSim":
        img_url_list = chapter_code.select("div[class='vung_doc'] img")
    elif website == "MangaNelo":
        img_url_list = chapter_code.select("div[class='vung-doc'] img")
    return img_url_list

#returns the URL of the next chapter after processing the current one
def go_to_next_chapter(url, website):
    chapter_code = get_source_code(url)
    if "NEXT CHAPTER" in chapter_code.text:
        if website == "MangaSim":
            next_chapter = chapter_code.select("div[class='panel-btn-changes'] a")[1]
        elif website == "MangaNelo":
            next_chapter = chapter_code.select("div[class='btn-navigation-chap'] a[class='back']")[1]
        return next_chapter.get("href")
    else:
        return None


### functions just to be extra ###


def done_message(start_time):
    end_time = time.time()
    download_minutes = (end_time-start_time) // 60
    download_seconds = (end_time-start_time) - (download_minutes*60)
    line_break()
    print(f"The download took {round(download_minutes)} minutes and {round(download_seconds)} seconds.")

def line_break():
    print("x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x")


### functions in main() ###


def get_manga_input():
    input_title = input("Which manga would you like to download?: ")    #gets user input for what manga he's searching for
    line_break()
    search_page_url = "http://mangasim.com/search/" + input_title.replace(" ", "_")     #passes it to MangaSim's manga search engine
    search_page_code = get_source_code(search_page_url)
    title_list = search_page_code.select("h2[class='story-name'] a")
    if title_list == []:    #MangaSim search engine returns a blank
        print("We couldn't find the manga you were looking for. Try searching with another keyword.")
        line_break()
        main()
    else:   #at least one manga shows up on the search engine
        info_list = search_page_code.select("div[class='story-item'] span")
        return title_list, info_list    #returns the manga info to display to the reader

def get_manga_option(title_list, info_list):
    for i in range(len(title_list)):    #iterates through MangaSim's search results until the user finds the manga they were looking for
        title = title_list[i]  
        author = info_list[3*i]     
        last_updated = info_list[3*i+1]     
        print("Title : " + title.text)  #prints title
        print(author.text)              #prints author name
        print(last_updated.text)        #prints when the manga was last updated
        line_break()
        
        while True:
            input_break = input("Is this the manga you were looking for? (Type [Y]es or [N]o): ").upper()
            line_break()
            if input_break == "YES" or input_break == "Y":  #user has found the manga they were looking for
                return title.text, title.get("href")        #returns the manga title and URL
            elif input_break == "NO" or input_break == "N":
                break
            else:
                print("Please type 'yes' or 'no'.")
                line_break()
    else:   #user is unable to find the manga they were looking for among the search results
        print("We couldn't find the manga you were looking for. Try searching with another keyword.")
        line_break()
        main()
        
#for some manga, MangaSim redirects you to MangaNelo so we need to determine if it does
def get_website(url):
    if "mangasim" in url:
        return "MangaSim"
    elif "manganelo" in url:
        return "MangaNelo"

#returns the URL of a manga chapter
def get_chapter_url(url, website):
    while True:
        chapter_input = input("Begin installing from which chapter? (Type # to download from the start): ")
        line_break()
    
        if chapter_input == "#":
            content_page_code = get_source_code(url)
            if website == "MangaSim":
                chapter_list = content_page_code.select("div[class='chapter_list'] a")
            elif website == "MangaNelo":
                chapter_list = content_page_code.select("div[class='chapter-list'] a")
            first_chapter = chapter_list[::-1][0]
            chapter_url = first_chapter.get("href")
            return chapter_url
        
        elif chapter_input.isdigit():
            if website == "MangaSim":
                chapter_url = f"{url}/chapter_{chapter_input}"
            elif website == "MangaNelo":
                chapter_url = f"{url[:21]}/chapter/{url[28:]}/chapter_{chapter_input}"
            if get_image_links(chapter_url, website) == []:
                print("This chapter number doesn't exist. Please try again.")
                line_break()
                continue
            return chapter_url
        
        else:
            print("Please type in a number.")
            line_break()

#the actual downloading of the manga images into the chapter subfolder
def download_manga(url, website, folder):
    start_time = time.time()
    
    while True:
        subfolder = create_subfolder(folder, url)
        if os.path.isdir(subfolder):
            done_message(start_time)
            break
        else:
            os.makedirs(subfolder, exist_ok=True)
            print(f"Downloading from {url}...")
            img_url_list = get_image_links(url, website)
        
        for i in range(len(img_url_list)):
            img_url = img_url_list[i].get("src")
            img = requests.get(img_url)
            img.raise_for_status
            img_title = f"Part {i+1}.jpg"
            img_file = open(os.path.join(subfolder, img_title), "wb")
            for chunk in img.iter_content(100000):
                img_file.write(chunk)
            img_file.close
        
        next_chapter_link = go_to_next_chapter(url, website)
        if next_chapter_link != None:
            url = next_chapter_link
        else:
            done_message(start_time)
            break


### yeet ###


def main():
    title_list, info_list = get_manga_input()                           #get user's search input; returns search results
    manga_title, manga_url = get_manga_option(title_list, info_list)    #displays the search results, iterating till the user finds what he was looking for; returns title and URL
    website_name = get_website(manga_url)                               #finds out whether the manga is sourced from MangaSim or MangaNelo
    chapter_url = get_chapter_url(manga_url, website_name)              #according to the user's input, it returns the URL of the __th chapter to the manga
    manga_folder = create_parent_folder(manga_title)                    #creates the appropriate folders to store the manga images
    download_manga(chapter_url, website_name, manga_folder)             #downloads the image links to the manga from the __th chapter, then onwards

if __name__ == "__main__":
    main()
    input()     #to prevent the window from automatically closing after the download finishes
