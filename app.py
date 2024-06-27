from flask import Flask, request, render_template, g, send_file
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
from waitress import serve
import sqlite3
import base64
import os   
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config['DATABASE'] = os.path.join(app.root_path, 'database.db')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

with app.app_context():
    db = get_db()
    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    db.commit()

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()
#---------------------------------------------------------------------------------------------------------
def dateConv(date_str):
    date_format = "%Y-%m-%d %H:%M:%S"
    date_obj = datetime.strptime(str(date_str), date_format)
    reference_date = datetime(2024, 6, 5)
    delta = date_obj - reference_date
    return delta.days

def Table(IV):
    db = get_db()
    curs=db.cursor()

    if IV == 'control':
        rang = range(1,9)
    if IV == 'ph5':
        rang = range(9,11)
    if IV == 'ph5.5':
        rang = range(11,13)
    if IV == 'ph7':
        rang = range(13,15)
    if IV == 'ph7.5':
        rang = range(15,17)
    if IV == 'CM2':
        rang = range(17,21)
    if IV == 'CM4':
        rang = range(21,25)
    if IV == 'LI':
        rang = range(25,33)

    if IV == 'control':
        table = 'Control'
    elif 'ph' in IV:
        table = 'PH'
    elif 'CM' in IV:
        table = 'CalMag'
    else:
        table = 'LI'

    days = ["Days Since Start"]
    numbers = ["Plant #"]
    heights = ["Plant Height(cm)"]
    lsizes = ["Leaf Size(cm)"]
    ECs = ["Electrical Conductivity(ppm)"]
    deficiencies = ["Plant Deficiencies/Notes"]
    for x in rang:
        curs.execute("SELECT height FROM "+table+" WHERE PN = ?",(str(x),))
        heightresult = curs.fetchall()
        heightresult = [row[0] for row in heightresult]
        curs.execute("SELECT leafSize FROM "+table+" WHERE PN = ?",(str(x),))
        leafresult = curs.fetchall()
        leafresult = [row[0] for row in leafresult]
        curs.execute("SELECT EC FROM "+table+" WHERE PN = ?",(str(x),))
        ECresult = curs.fetchall()
        ECresult = [row[0] for row in ECresult]
        curs.execute("SELECT deficiencies FROM "+table+" WHERE PN = ?",(str(x),))
        dresult = curs.fetchall()
        dresult = [row[0] for row in dresult]
        curs.execute("SELECT created FROM "+table+" WHERE PN = ?",(str(x),))
        timeresult = curs.fetchall()
        timeresult = [row[0] for row in timeresult]

        for y in range(0,len(heightresult)):
            numbers.append(x)
            if(heightresult[y]=='' or heightresult[y]==' '):
                heightresult[y] = 'N/A'
            heights.append(heightresult[y])
            if(leafresult[y]=='' or leafresult[y]==' '):
                leafresult[y] = 'N/A'
            lsizes.append(leafresult[y])
            if(ECresult[y]=='' or ECresult[y]==' '):
                ECresult[y] = 'N/A'
            ECs.append(ECresult[y])
            if(dresult[y]=='' or dresult[y]==' '):
                dresult[y] = 'N/A'
            deficiencies.append(dresult[y])
            days.append(timeresult[y])

    for x in range(1,len(days)):
        days[x] = dateConv(days[x])

    #form the table:
    lines = []
    for x in range(0,len(days)):
        lines.append([str(days[x]), str(numbers[x]), heights[x], lsizes[x], ECs[x], deficiencies[x]])

    font = ImageFont.truetype(font="arial.ttf", size=16)
    font_size = 16

    img_width = 1000
    img_height = (len(lines)-1) * (font_size + 2) + 19

    image = Image.new('RGB', (img_width, img_height), 'white')
    draw = ImageDraw.Draw(image)

    draw.line((0,0,0,img_height), fill=(0,0,0))
    draw.line((0,img_height,img_width,img_height), fill=(0,0,0))
    draw.line((0,0,img_width,0), fill=(0,0,0))
    draw.line((img_width,0,img_width,img_height), fill=(0,0,0))

    y = 1
    x = 1
    for line in lines:
        it = 0
        for col in line:
            draw.text((x, y), col, (0,0,0), font=font)
            x+=len(lines[0][it])*8+2
            if line == lines[0]:
                if col!="Plant Deficiencies/Notes":
                    draw.line((x-5,0,x-5,img_height), fill=(0,0,0))
            it+=1
        x = 1
        y += font_size + 1
        draw.line((0,y,img_width,y), fill=(0,0,0))
        y+=1
    
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='png')
    img_buffer.seek(0)

    return img_buffer

def Graph(IV, YDV):
    db = get_db()
    curs=db.cursor()
    #get control data
    controldata = []
    for x in range(1,9):
        curs.execute("SELECT "+YDV+" FROM Control WHERE PN = ?",(str(x),))
        dataresult = curs.fetchall()
        dataresult = [row[0] for row in dataresult]
        curs.execute("SELECT created FROM Control WHERE PN = ?",(str(x),))
        timeresult = curs.fetchall()
        timeresult = [row[0] for row in timeresult]
        for y in range(0,len(dataresult)):
            if(dataresult[y]!='' and dataresult[y]!=' '):
                set = [dataresult[y],timeresult[y]]
                controldata.append(set)

    #get experimental data
    if IV == 'ph5':
        rang = range(9,11)
    if IV == 'ph5.5':
        rang = range(11,13)
    if IV == 'ph7':
        rang = range(13,15)
    if IV == 'ph7.5':
        rang = range(15,17)
    if IV == 'CM2':
        rang = range(17,21)
    if IV == 'CM4':
        rang = range(21,25)
    if IV == 'LI':
        rang = range(25,33)
    
    if 'ph' in IV:
        table = 'PH'
    elif 'CM' in IV:
        table = 'CalMag'
    else:
        table = 'LI'

    experimentaldata = []
    for x in rang:
        curs.execute("SELECT "+YDV+" FROM "+table+" WHERE PN = ?",(str(x),))
        dataresult = curs.fetchall()
        dataresult = [row[0] for row in dataresult]
        curs.execute("SELECT created FROM "+table+" WHERE PN = ?",(str(x),))
        timeresult = curs.fetchall()
        timeresult = [row[0] for row in timeresult]
        for y in range(0,len(dataresult)):
            if(dataresult[y]!='' and dataresult[y]!=' '):
                set = [dataresult[y],timeresult[y]]
                experimentaldata.append(set)

    avgcontroldata = []
    groups = {}
    for pair in controldata:
        if pair[1] not in groups:
            groups[pair[1]] = [pair[0]]
        else:
            groups[pair[1]].append(pair[0])
    for day, vals in groups.items():
        sum = 0
        for val in vals:
            sum+=float(val)
        avg = sum/len(vals)
        avgcontroldata.append([avg,day])

    avgexperimentaldata = []
    groups = {}
    for pair in experimentaldata:
        if pair[1] not in groups:
            groups[pair[1]] = [pair[0]]
        else:
            groups[pair[1]].append(pair[0])
    for day, vals in groups.items():
        sum = 0
        for val in vals:
            sum+=float(val)
        avg = sum/len(vals)
        avgexperimentaldata.append([avg,day])
    
    
    line1x = []
    for pair in avgcontroldata:
        line1x.append(pair[1])

    line1y = []
    for pair in avgcontroldata:
        line1y.append(pair[0])
    
    line2x = []
    for pair in avgexperimentaldata:
        line2x.append(pair[1])
    
    line2y = []
    for pair in avgexperimentaldata:
        line2y.append(pair[0])

    for x in range(0,len(line1x)):
        line1x[x] = dateConv(line1x[x])
    
    for x in range(0,len(line2x)):
        line2x[x] = dateConv(line2x[x])

    plt.plot(line1x, line1y, label='Control', color='blue') 
    plt.plot(line2x, line2y, label=IV, color='red')
    plt.xlabel('Days Since Experiment Start')
    plt.ylabel(YDV)
    plt.title('Change in '+YDV+' Over Time')
    plt.legend()  

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)

    plt.close()

    return img_buffer
#---------------------------------------------------------------------------------------------------------

@app.route('/')
def aboutPage():
    return render_template('home/homeabout.html')
@app.route('/home/data')
def dataPage():
    return render_template('home/homedata.html')
@app.route('/home/photos')
def photoPage():
    return render_template('home/homephotos.html')
@app.route('/home/resources')
def resourcePage():
    return render_template('home/homeresources.html')

@app.route('/tableapi/<IV>')
def sendTable(IV):
    buffer = Table(IV)
    return send_file(buffer, mimetype='image/png', as_attachment=False)

@app.route('/graphapi/<parameters>')
def sendGraph(parameters):
    Variables = parameters.split(',')
    buffer = Graph(Variables[0],Variables[1])

    return send_file(buffer, mimetype='image/png', as_attachment=False)

@app.route('/photodates/<plant>', methods=['GET'])
def photoDates(plant):
    db=get_db()
    cursor=db.cursor()
    cursor.execute('SELECT created FROM IMAGES WHERE PN = ?',(plant,))
    dates = cursor.fetchall()
    dates = [row[0] for row in dates]

    dateString=""
    for date in dates:
        dateString+=str(dateConv(date))
        if date!=dates[len(dates)-1]:
            dateString+=','
    return dateString

@app.route("/blobdata/<parameters>")
def BLOBdata(parameters):    
    parameters=parameters.split(',')
    plant = parameters[0]
    day = parameters[1]

    db=get_db()
    cursor=db.cursor()

    cursor.execute("SELECT * FROM Images WHERE PN = ?", (plant,))
    result = cursor.fetchall()
    times = [row[1] for row in result]
    blobs = [row[3] for row in result]

    for index, time in enumerate(times):
        if dateConv(time)==int(day):
            return blobs[index]
    
@app.route('/graphapi')
def placeholder():
    return send_file('images/Loading.png', mimetype='image/png')

@app.route('/tableapi')
def tableplaceholder():
    return send_file('images/Loading.png', mimetype='image/png')

@app.route ('/photodates')
def datesplaceholder():
    return send_file('images/Loading.png', mimetype='image/png')

@app.route('/blobdata')
def BLOBPlaceholder():
    return send_file('images/Loading.png', mimetype='image/png')

@app.route('/uploaddata')
def selectPlant():
    return render_template("selectPlant.html")

@app.route('/successimage')
def image():
    return send_file("images/success.JPG", mimetype='image/jpeg')

@app.route('/log', methods = ['POST'])
def receiveData():
    message = request.form['text_to_send']
    return render_template('logdata.html',message=message)

@app.route('/upload', methods = ['POST'])
def uploadData():
    stringData = request.form['text_to_send']
    blob_string1 = request.form['blob_to_send']
    blob_string2 = request.form['blob_to_send2']
    blob_string3 = request.form['blob_to_send3']
    db = get_db()
    curs = db.cursor()    

    stringData = stringData.replace('"',"")
    data = stringData.split(',')

    if stringData[1]!="" or stringData[2]!="" or stringData[3]!="" or stringData[4]!="":
        plant = int(data[0])
        height = data[1]
        leafSize = data[2]
        EC = data[3]
        deficiencies = data[4]

        if plant<9:
            table = "Control"
        elif plant<17:
            table = "pH"
        elif plant<25:
            table = "CalMag"
        else:
            table = "LI"

        curs.execute(f"SELECT * FROM {table} WHERE PN = ?",(plant,))
        rows = curs.fetchall()
        addedToday = False
        for row in rows:
            timestamp = row[1].date()
            if timestamp == datetime.now().date():
                addedToday = True
                id = row[0]

        if addedToday:
            if(height!=""):
                db.execute(f"UPDATE {table} SET height = ? WHERE id = ?",(height,id,))
            if(leafSize!=""):
                db.execute(f"UPDATE {table} SET leafSize = ? WHERE id = ?",(leafSize,id,))
            if(EC!=""):
                db.execute(f"UPDATE {table} SET EC = ? WHERE id = ?",(EC,id,))
            if(deficiencies!=""):
                db.execute(f"UPDATE {table} SET deficiencies = ? WHERE id = ?",(deficiencies,id,))
            db.commit()

        else:    
            db.execute(f'INSERT INTO {table} (PN, EC, height, leafSize, deficiencies) VALUES (?, ?, ?, ?, ?)', (plant, EC, height, leafSize, deficiencies))
            db.commit()
    
    if blob_string1!="":
        blob_string1=blob_string1[:-1]
        blob_string2=blob_string2[1:]
        blob_string2=blob_string2[:-1]
        blob_string3=blob_string3[1:]
        blob_string = blob_string1+','+blob_string2+','+blob_string3

        db.execute(f"INSERT INTO Images (Image, PN) VALUES (?, ?)",(blob_string, plant,))
        db.commit()


    return render_template("logdatasuccess.html")
#---------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    #serve(app,host = '0.0.0.0',port = 5000)
    #app.run(host='0.0.0.0')
    app.run(debug=True,host='0.0.0.0')

