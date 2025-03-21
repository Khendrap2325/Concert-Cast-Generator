import pandas as pd
import random
from collections import defaultdict
from flask import Flask, request, render_template

app = Flask(__name__)

def scheduler(df, dance_req=3, dance_limits=None, mandatory_dances=None):
    """
    Outputs a dance concert cast list
    :param dance_req: The required amount of dances for each dancer
    """

    #read the dance response form
    df = df.iloc[:, 1:] #ignore default google sheet timestamp column 
    df.fillna('No', inplace=True)
    df.columns = df.columns.str.strip()

    #Extract dancer information
    dancers = df[['name', 'classification']] #Name and classification columns
    dance_preferences = df.iloc[:, 2:] #song titles
    dance_assignments = defaultdict(list)
    dancer_load = {name: 0 for name in dancers['name']} #keeps track of how many dances each dancer has

    #assign mandatory dances
    if mandatory_dances:
        for classification, mandatory_dance in mandatory_dances.items():
            mandatory_dancers = dancers[dancers['classification']== classification]['name'].tolist()
            for name in mandatory_dancers:
                if len(dance_assignments[mandatory_dance]) < dance_limits.get(mandatory_dance, (0, float('inf')))[1]:
                    dance_assignments[mandatory_dance].append(name)
                    dancer_load[name] +=1
    #distinguish senior and new members
    seniors = dancers[dancers['classification'] =='OG (Senior)']['name'].tolist()
    new_members = dancers[dancers['classification'] == 'New Member']['name'].tolist()
    gen_members = dancers[dancers['classification'] == 'OG (Non-Senior)']['name'].tolist()

    random.shuffle(seniors)
    random.shuffle(new_members)
    random.shuffle(gen_members)

    for name in seniors + gen_members + new_members:
        available_dances = [dance for dance in dance_preferences.columns if df.loc[df['name'] == name, dance].values[0] == 'Yes']
        random.shuffle(available_dances) #shuffles dances but there is no cap on dances so thst needs to be added
        assigned_count = 0

        while assigned_count < dance_req and available_dances:
            dance = available_dances.pop()
            if dance_limits and len(dance_assignments[dance]) < dance_limits.get(dance, (0,float('inf')))[1]:
                dance_assignments[dance].append(name)
                dancer_load[name] +=1
                assigned_count += 1

    for dance in dance_preferences.columns:
        min_dancers, max_dancers = dance_limits.get(dance, (0, float('inf')))  
        potential_dancers = [name for name in dancers['name'] if df.loc[df['name'] == name, dance].values[0] == 'Yes' and dancer_load[name] < dance_req]
        random.shuffle(potential_dancers)

        for name in potential_dancers:
            if len(dance_assignments[dance]) < max_dancers:
                dance_assignments[dance].append(name)
                dancer_load[name] += 1
    
    #output
    with open('dance_cast_list.txt', 'w') as f:
        f.write("Dance Assignments:\n")
        for dance, assigned_dancers in dance_assignments.items():
            f.write(f"{dance}: {', '.join(assigned_dancers)}\n")
        f.write("\nNumber of Dances Each Dancer is in:\n")
        for name, load in dancer_load.items():
            f.write(f"{name}: {load} dances\n")

   # print("Dance assignments have been saved to dance_cast_list.txt")
    return dance_assignments

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        if 'file' not in  request.files:
            return "Nol file uploaded", 400
        file = request.files['file']
        if file.filename == '':
            return "No file selected", 400
        df = pd.read_csv(file)
        dance_limits = {
            "You're Good by Miranda Curtis" : (16, 20),
            "Elohim by Eddie James" : (11, 15),
            "The Call by Isabel Davis" : (8, 10),
            "Purify by ELEVATION RHYTHM" : (16, 20),
            "Free by Kierra Sheard" : (11, 15),
            "All Things by New Tye Tribbett (mandatory for ALL Beacon babies to check)" : (25, 35),
            '"Bless the Lord/Everything Part I, Part II by Tye Tribbett"' : (16, 20),
            "This is the Gospel by Elevation Rhythm" : (11, 15),
            "His Words by Grace Tena": (8, 10),
            "I Am by Jason Nelson" : (16, 20),
            "Senior Piece (mandatory for ALL seniors to check)" : (13, 13),
            "Indescribable by Kierra Sheard": (8, 10),
        }
        mandatory_dances = {
            'New Member' : 'All Things by New Tye Tribbett (mandatory for ALL Beacon babies to check)',
            'OG (Senior)' : 'Senior Piece (mandatory for ALL seniors to check)'
        }

        assignments = scheduler(df, dance_limits=dance_limits, mandatory_dances=mandatory_dances)
        return render_template('results.html', assignments=assignments)
    return render_template('upload.html')
#csv_file = "dance_response_form.csv"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)


    



