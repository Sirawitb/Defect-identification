#!/usr/bin/env python
# coding: utf-8

# # Failure Attribute Analysis - version 0.2 GUI

# In[1]:


from IPython.display import HTML, Javascript, display

def initialize():
    display(HTML(
        '''
            <script>
                code_show = false;
                function restart_run_all(){
                    IPython.notebook.kernel.restart();
                    setTimeout(function(){
                        IPython.notebook.execute_all_cells();
                    }, 10000)
                }
                function code_toggle() {
                    if (code_show) {
                        $('div.input').hide(200);
                    } else {
                        $('div.input').show(200);
                    }
                    code_show = !code_show
                }
            </script>
            <button onclick="restart_run_all()">Reset and Start Again</button>
        '''
    ))
initialize()


# Step 1 - Upload your excel file containing drive serial numbers and thier status ([Click to see excel template](https://seagatetechnology-my.sharepoint.com/:x:/r/personal/sirawit_pruksawan_seagate_com/Documents/Data.csv?d=w82405581f1ba4384840334c91ab74eb5&csf=1&web=1&e=cB9Br1)) 

# In[2]:


# set base batch id
from datetime import datetime

PROCESSING_CORE = 300
BASE_BATCH_ID = str(datetime.now())

import ipywidgets as widgets
from ipywidgets import FileUpload, Output

out = Output()

@out.capture()
def show_content(change):
    print("Your file", str(change['new'].keys())[9:],"has been uploaded")

w = FileUpload(accept='.csv', multiple=False)
w.observe(show_content, 'value')
with out:
    display(w)
out


# Step 2 - Input Username and Password of logservice website below

# In[3]:


User = widgets.Password(description="Username", width=200)
Pass = widgets.Password(description='Password:', width=200)
display(User)
display(Pass)

from IPython.display import Javascript, display


# In[4]:


def run_all(ev):
    display(Javascript('IPython.notebook.execute_cells_below()'))

button = widgets.Button(description="Generate result")
button.on_click(run_all)
display(button)


# In[5]:


import warnings
warnings.simplefilter('ignore')
import sys
import pandas as pd

with open("Data.csv", "w+b") as i:
    if len(w.data) > 0:
        i.write(w.data[0])
    else:
        print("Please complete all required information")
        sys.exit()
        
x=pd.read_csv('Data.csv', index_col=None)


# import Pass/fail data
import pandas as pd
import numpy as np
SERIALNUMBER = x
SERIALNUMBER = SERIALNUMBER.drop(['STATUS'], axis=1)
SERIALNUMBER_chunk = np.array_split(SERIALNUMBER.values.reshape(-1), PROCESSING_CORE)
#SERIALNUMBER_chunk[0].shape

# Log in to Logservice web and generate attribute sheet
import getpass
import requests
import multiprocessing
import lib.data_preparation as dp

USER = User.value
PASS = Pass.value

for chunk_id in range(PROCESSING_CORE):
    
    SESSION = requests.session()
    SESSION.post('http://kor.log.seagate.com/LogService/Login.aspx?ReturnUrl=%2fLogService%2f', data = {
        'm_textboxUserName' : USER,
        'm_textboxPassword' : PASS
    })
    
    m = multiprocessing.Process(
        target = dp.run,
        args = (
            SESSION, BASE_BATCH_ID, SERIALNUMBER_chunk[chunk_id].tolist(),
        )
    ).start()
    
# combine all attribute sheets into one file
import pandas as pd
import glob
    
path = './__tmp__/' # use your path
all_files = glob.glob(path + BASE_BATCH_ID +"/*.csv")

li = []

import os
str_directory = path + BASE_BATCH_ID
list_files = [x for x in os.listdir(str_directory) if x[0]!='.']
for each_file in list_files:
    file_path = '%s/%s' % (str_directory, each_file)
    if os.path.getsize(file_path)==0:
        os.remove(file_path)
    else:
        pass
all_files = glob.glob(path + BASE_BATCH_ID +"/*.csv")
    
for filename in all_files:
    df = pd.read_csv(filename, index_col=None, header=0, )
    li.append(df)

frame = pd.concat(li, axis=0, ignore_index=True)

df = pd.read_csv('Data.csv', index_col=None, header=0)
frame = frame.set_index('SERIAL_NUM').join(df.set_index('SERIAL_NUM'))
frame.to_excel('Full_raw_data.xlsx', index=True)


# In[ ]:


dt = pd.read_excel('Full_raw_data.xlsx', index_col=None, header=0)
dt = dt.drop(['DRIVE_ATTRIBUTES*'], axis=1)
dt = dt.loc[:, ~dt.columns.str.contains('^Unnamed')]
dt = dt.iloc[1:]
data=dt.replace(np.NaN,"NaN")
#list=['BIRTH_DATE','EVENT_DATE','TEST_DATE','BIRTH_DATE.1','LUBE1_DATE', 'LUBE1_DATE_2', 'LUBE1_DATE_3', 'LUBE1_DATE_6', 'LUBE1_DATE_7', 'LUBE1_DATE_8', 'MDW_TEST_DATE', 'MDW_TEST_DATE_2', 'MDW_TEST_DATE_3', 'MDW_TEST_DATE_4', 'MDW_TEST_DATE_5', 'MDW_TEST_DATE_6', 'MDW_TEST_DATE_7', 'MDW_TEST_DATE_8']
list=['LUBE1_DATE_2']
for col in list: 
    DATE_col= col
    data=data.sort_values(by=[DATE_col], ascending=True)
    data['LEVEL_'+DATE_col] = np.rint(data.index.values/(len(data)/5))
    data

    conditions = [
        (data['LEVEL_'+DATE_col] == 0),
        (data['LEVEL_'+DATE_col] == 1),
        (data['LEVEL_'+DATE_col] == 2),
        (data['LEVEL_'+DATE_col] == 3),
        (data['LEVEL_'+DATE_col] == 4),
        (data['LEVEL_'+DATE_col] == 5)
        ]

    values = ['Time 1', 'Time 2', 'Time 3', 'Time 4', 'Time 5', 'Time 6']

    data['TIME_'+DATE_col] = np.select(conditions, values)

    data=data.drop(['LEVEL_'+DATE_col], axis=1)
    data=data.drop([DATE_col], axis=1)
    data

df = pd.DataFrame(columns = ['Attribute'])
maxt = 0

max
for col in data.columns: 
    d1 = data.groupby([col, "STATUS"])["STATUS"].count().unstack(1)
    d1 = d1.replace(np.NaN,0)
    #print(d1)
    if np.size(d1,1) > 0 and len(d1) > 0 and col != "STATUS":
        d1["Diff"] = d1["F"]-d1["P"]
        d1["Ratio"] = 100*d1["F"]/(d1["P"]+d1["F"])
        maxdif = np.nanmax(d1['Diff'])
        maxratio = np.nanmax(d1['Ratio'])
        meandif = np.nanmean(d1['Diff'])
        
        d2 = d1.loc[d1['Ratio'] != np.inf]
        meanratio = np.nanmean(d2['Ratio'])    
        
        d1.head()  
        #print(d1)
        #print("mean ratio", meanratio)
        d1 = d1.loc[d1['Diff'] >= meandif]
        d1 = d1.loc[d1['Ratio'] >= meanratio]
        d1 = d1.loc[d1['Diff'] == maxdif]
        m=d1['Diff'].max()
        n=d1['Ratio'].max()
        df=df.append({'Attribute':col, 'Max surplus fail quantity':m, 'Max fail rate':n}, ignore_index=True)
    #print(col)
    #print(d1)
rank_mfr = df.sort_values(by=['Max surplus fail quantity', 'Max fail rate'], ascending=[False, False])
rank_mfr = rank_mfr.loc[rank_mfr['Max surplus fail quantity'] >= np.nanmean(rank_mfr['Max surplus fail quantity'])]
rank_mfr = rank_mfr.loc[rank_mfr['Max fail rate'] >= np.nanmean(rank_mfr['Max fail rate'])]
rank_mfr = rank_mfr.reset_index(drop=True)
rank_msfq = df.sort_values(by=['Max fail rate', 'Max surplus fail quantity'], ascending=[False, False])
rank_msfq = rank_msfq.loc[rank_msfq['Max surplus fail quantity'] >= np.nanmean(rank_msfq['Max surplus fail quantity'])]
rank_msfq = rank_msfq.loc[rank_msfq['Max fail rate'] >= np.nanmean(rank_msfq['Max fail rate'])]
rank_msfq = rank_msfq.reset_index(drop=True)


# In[ ]:


df.to_csv('Summary_table.csv', index=False)

get_ipython().run_line_magic('matplotlib', 'inline')
import matplotlib.pyplot as plt
import pandas as pd
import ipywidgets as widgets
import numpy as np
from ipywidgets.widgets.interaction import show_inline_matplotlib_plots

from IPython.core.display import display, HTML
display(HTML("<style>div.output_scroll { height: 30em; }</style>"))

out1 = widgets.Output()
out2 = widgets.Output()
out3 = widgets.Output()

tab = widgets.Tab(children = [out1, out2, out3])
tab.set_title(0, 'Summary Graph')
tab.set_title(1, 'Summary Table')
tab.set_title(2, 'Download')
display(tab)
with out1:
    dropdown_year2 = widgets.Dropdown(options = ['Select result type','Result based on surplus fail quantity', 'Result based on fail rate'])
    output_year2 = widgets.Output()
    xy = 15
    def dropdown_year_eventhandler2(change):
        output_year2.clear_output()
        with output_year2:
            if (change.new == "Result based on surplus fail quantity"):
                for n in range (xy):
                    d1 = data.groupby([str(rank_mfr['Attribute'].iloc[n]), "STATUS"])["STATUS"].count().unstack(1)
                    color_list = ['r', 'g']
                    d1.plot(kind="bar", color=color_list, title="Attribute: " + str(rank_mfr['Attribute'].iloc[n]))              
                    show_inline_matplotlib_plots()
            if (change.new == "Result based on fail rate"):
                for n in range (xy):
                    d1 = data.groupby([str(rank_msfq['Attribute'].iloc[n]), "STATUS"])["STATUS"].count().unstack(1)
                    color_list = ['r', 'g']
                    d1.plot(kind="bar", color=color_list, title="Attribute: " + str(rank_msfq['Attribute'].iloc[n]))
                    show_inline_matplotlib_plots()       
    dropdown_year2.observe(dropdown_year_eventhandler2, names='value')
    display(dropdown_year2)
    display(output_year2)
    
with out2:    

    dropdown_year = widgets.Dropdown(options = ['Select table type','Sort by Max surplus fail quantity', 'Sort by Max fail rate'])
    output_year = widgets.Output()
    
    def dropdown_year_eventhandler(change):
        output_year.clear_output()
        with output_year:
            if (change.new == "Sort by Max surplus fail quantity"):                
                display(pd.DataFrame(rank_mfr))
            if (change.new == "Sort by Max fail rate"):
                display(pd.DataFrame(rank_msfq))
    pd.set_option('display.max_rows', None, 'display.max_columns', None)        
    dropdown_year.observe(dropdown_year_eventhandler, names='value')
    display(dropdown_year)
    display(output_year)
    
with out3:      
    from IPython.display import FileLink
    display(FileLink('Full_raw_data.xlsx'))
    display(FileLink('Summary_table.csv'))
    


# In[ ]:


from IPython.display import HTML

HTML('''<script>
  function code_toggle() {
    if (code_shown){
      $('div.input').hide('500');
      $('#toggleButton').val('Display code')
    } else {
      $('div.input').show('500');
      $('#toggleButton').val('Hide Code')
    }
    code_shown = !code_shown
  }

  $( document ).ready(function(){
    code_shown=false;
    $('div.input').hide()
  });
</script>
<form action="javascript:code_toggle()"><input type="submit" id="toggleButton" value="Display code"></form>''')


# In[ ]:


dt = pd.read_excel('Full_raw_data.xlsx', index_col=None, header=0)
dt = dt.drop(['DRIVE_ATTRIBUTES*'], axis=1)
dt = dt.loc[:, ~dt.columns.str.contains('^Unnamed')]
dt = dt.iloc[1:]
data=dt.replace(np.NaN,"NaN")


# In[ ]:


#list=['BIRTH_DATE','EVENT_DATE','TEST_DATE','BIRTH_DATE.1','LUBE1_DATE', 'LUBE1_DATE_2', 'LUBE1_DATE_3', 'LUBE1_DATE_6', 'LUBE1_DATE_7', 'LUBE1_DATE_8', 'MDW_TEST_DATE', 'MDW_TEST_DATE_2', 'MDW_TEST_DATE_3', 'MDW_TEST_DATE_4', 'MDW_TEST_DATE_5', 'MDW_TEST_DATE_6', 'MDW_TEST_DATE_7', 'MDW_TEST_DATE_8']


# In[15]:


import voila


# In[14]:


print (tornado.version)


# In[ ]:




