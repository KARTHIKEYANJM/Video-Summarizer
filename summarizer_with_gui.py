###################################################################################
# Module Imports
import re
import webvtt
from gensim.summarization.summarizer import summarize as gensim_based
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import nltk
from tkinter import *
from tkinter import filedialog
import tkinter.font as tkFont
import os
import youtube_dl
import pandas as pd
import numpy as np
import spacy
nlp = spacy.load("en_core_web_sm")

####################################################################################
# Function Block

def get_caption(url):
    global video_title
    # Using Youtube-dl inside python
    ydl_opts = {
        'skip_download': True,        # Skipping the download of actual file
        'writesubtitles': True,       # Uploaded Subtitles
        "writeautomaticsub": True,    # Auto generated Subtitles
        "subtitleslangs": ['en'],     # Language Needed "en"-->English
        'outtmpl': 'test.%(ext)s',    # Saving downloaded file as 'test.en.vtt'
        'nooverwrites': False,        # Overwrite if the file exists
        'quiet': True                # Printing progress
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get('title', None)
        except:
            print("Try with a YouTube URL")
    corpus = []
    for caption in webvtt.read('test.en.vtt'):
        corpus.append(caption.text)
    corpus = "".join(corpus)
    corpus = corpus.replace('\n', ' ')

    return corpus


def summarizer(text, option, fraction):
    # "Tf-IDF-Based", "Frequency-Based", "Gensim-Based"
    
    frac=fraction
    if option == "TfIdf-Based":
        return tfidf_based(text, frac)
    if option == "Frequency-Based":
        return freq_based(text, frac)
    if option == "Gensim-Based":
        doc=nlp(text)
        text="\n".join([sent.text for sent in doc.sents])
        return gensim_based(text=text, ratio=frac)

def tfidf_based(msg,fraction=0.3):
    # Creating Pipeline
    doc=nlp(msg)
    
    #Sent_tokenize
    sents =[sent.text for sent in doc.sents]
    
    #Number of Sentence User wants
    num_sent=int(np.ceil(len(sents)*fraction))
    
    #Creating tf-idf removing the stop words matching token pattern of only text
    tfidf=TfidfVectorizer(stop_words='english',token_pattern='(?ui)\\b\\w*[a-z]+\\w*\\b')
    X=tfidf.fit_transform(sents)
    
    #Creating a df with data and tf-idf value
    df=pd.DataFrame(data=X.todense(),columns=tfidf.get_feature_names())
    indexlist=list(df.sum(axis=1).sort_values(ascending=False).index)
#     indexlist=list((df.sum(axis=1)/df[df>0].count(axis=1)).sort_values(ascending=False).index)
    
    # Subsetting only user needed sentence
    needed = indexlist[:num_sent]
    
    #Sorting the document in order
    needed.sort()
    
    #Appending summary to a list--> convert to string --> return to user
    summary=[]
    for i in needed:
        summary.append(sents[i])
    summary="".join(summary)
    summary = summary.replace("\n",'')
    return summary


def freq_based(text, fraction):
    # Convert to pipeline
    doc = nlp(text)
    # Break to sentences
    sentence = [sent for sent in doc.sents]
    # Number of sentence user wants
    numsentence = int(np.ceil(fraction*len(sentence)))

    # Tokenizing and filtering key words
    words = [word.text.lower()
             for word in doc.doc if word.is_alpha and word.is_stop == False]
    # Converting to df for calculating weighted frequency
    df = pd.DataFrame.from_dict(
        data=dict(Counter(words)), orient="index", columns=["freq"])
    df["wfreq"] = np.round(df.freq/df.freq.max(), 3)
    df = df.drop('freq', axis=1)

    # Convert weighted frequency back to dict
    wfreq_words = df.wfreq.to_dict()

    # Weight each sentence based on their wfreq
    sent_weight = []
    for sent in sentence:
        temp = 0
        for word in sent:
            if word.text.lower() in wfreq_words:
                temp += wfreq_words[word.text.lower()]
        sent_weight.append(temp)
    wdf = pd.DataFrame(data=np.round(sent_weight, 3), columns=['weight'])
    wdf = wdf.sort_values(by='weight', ascending=False)
    indexlist = list(wdf.iloc[:numsentence, :].index)

    # Summary
    sumlist = []
    for s in indexlist[:5]:
        sumlist.append(sentence[s])
    summary = ''.join(token.string.strip() for token in sumlist)
    return summary


##################################################################################
# GUI BLOCK
root = Tk(baseName="Video Summarizer")
root.title("Caption Based Video Summarizer")
root.configure(background='#009688')
root.geometry("600x400+400+200")
root.resizable(0, 0)

# Main Title Label
title = Label(root, text="Video Summarizer", font="bold 26",
              bg="#009688", padx=140, pady=10).grid(row=0, column=0)

# URL Label
url_label = Label(root, text="URL:", font="bold",
                  bg='#009688', justify="right", bd=1)
url_label.place(height=50, x=100, y=70)

# Model Label
model_label = Label(root, text="Model:", font="bold",
                    bg='#009688', justify="right", bd=1)
model_label.place(height=50, x=90, y=135)

# Fraction Label
fraction_label = Label(root, text="Fraction:", font="bold",
                       bg='#009688', justify="right", bd=1)
fraction_label.place(height=50, x=80, y=210)

# Folder Label
folder_label = Label(root, text="Location:", font="bold",
                     bg='#009688', justify="right", bd=1)
folder_label.place(height=50, x=75, y=280)

# Entry --> String
get_url = Entry(root, width=40)
get_url.place(width=300, height=30, x=150, y=80)

# DropDown
options = ["TfIdf-Based", "Frequency-Based", "Gensim-Based"]
# Declaring Variable and choosing default one
default_option = StringVar(root)
default_option.set(options[0])
drop = OptionMenu(root, default_option, *options)
drop.place(width=200, x=150, y=145)

# Entry --> Float
get_fraction = Entry(root, width=40)
get_fraction.place(width=300, height=30, x=150, y=220)

# Ask folder path
get_folder = Entry(root, width=40)
get_folder.place(width=300, height=30, x=150, y=290)

# Button --> Browse
folder = StringVar(root)


def browse():
    global folder
    folder = filedialog.askdirectory(initialdir='/')
    get_folder.insert(0, folder)


browse = Button(root, text="Browse", command=browse)
browse.place(height=30, x=475, y=290)


# Button Clear --> Reset all settings to default
def on_clear():
    default_option.set(options[0])
    get_url.delete(0, END)
    get_folder.delete(0, END)
    get_fraction.delete(0, END)


clear = Button(root, text="Clear", command=on_clear)
clear.place(width=50, x=240, y=350)
# Function on Submit


def on_submit():
    global url, choice, frac, current, folder
    url = get_url.get()
    choice = default_option.get()
    frac = float(get_fraction.get())
    current = os.getcwd()
    folder = get_folder.get()
    os.chdir(folder)
    print(url,choice,frac,folder)
    corpus = get_caption(url)
    with open("corpus.txt",'w+') as c:
        print(corpus,file=c)
    # Calling the main summarizer function
    summary = summarizer(corpus, choice, frac)
    filename = video_title+" "+choice+'.txt'
    filename = re.sub(r'[\/:*?<>|]', ' ', filename)
    with open(filename, 'w+') as f:
        print(summary, file=f)
    os.remove(os.getcwd()+'\\test.en.vtt')
    os.chdir(current)
    openpath = Button(root, text="Open Folder",
                      command=lambda: os.startfile(get_folder.get()))
    openpath.place(x=360, y=350)


# Button -->Submit
submit = Button(root, text="Submit", command=on_submit)
submit.place(width=50, x=300, y=350)

# Button Open Folder to view Saved files

root.mainloop()