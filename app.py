from flask import Flask, request, render_template, g, send_file
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
from waitress import serve
import sqlite3
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

    line1x = []
    for pair in controldata:
        line1x.append(pair[1])

    line1y = []
    for pair in controldata:
        line1y.append(pair[0])
    
    line2x = []
    for pair in experimentaldata:
        line2x.append(pair[1])
    
    line2y = []
    for pair in experimentaldata:
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
def homePage():
    return render_template('homepage.html')

@app.route('/tableapi/<IV>')
def sendTable(IV):
    buffer = Table(IV)
    return send_file(buffer, mimetype='image/png', as_attachment=False)

@app.route('/graphapi/<parameters>')
def sendGraph(parameters):
    Variables = parameters.split(',')
    buffer = Graph(Variables[0],Variables[1])

    return send_file(buffer, mimetype='image/png', as_attachment=False)

@app.route('/graphapi')
def placeholder():
    return send_file('images/Loading.png', mimetype='image/png')

@app.route('/tableapi')
def tableplaceholder():
    return send_file('images/Loading.png', mimetype='image/png')

@app.route('/uploaddata')
def selectPlant():
    return render_template("selectPlant.html")

@app.route('/successimage')
def image():
    return send_file("images/success.JPG", mimetype='image/jpeg')

@app.route('/image')
def farmImage():
    return send_file("images/farm.JPEG", mimetype='image/jpeg')

@app.route('/redirect', methods = ['POST'])
def receiveData():
    message = request.form['text_to_send']
    return render_template('logdata.html',message=message)

@app.route('/upload', methods = ['POST'])
def uploadData():
    stringData = request.form['text_to_send']
    stringData = stringData.replace('"',"")
    data = stringData.split(',')
    
    plant = int(data[0])
    height = data[1]
    leafSize = data[2]
    EC = data[3]
    deficiencies = data[4]
    db = get_db()
    if plant==9 or plant==10:
        ph = 5
    if plant==11 or plant==12:
        ph = 5.5
    if plant==13 or plant==14:
        ph = 7
    if plant==15 or plant==16:
        ph = 7.5
    if plant>=17 and plant<=20:
        CM = 2
    if plant>20 and plant<=24:
        CM = 4

    if plant<9:
        db.execute('INSERT INTO Control (PN, EC, height, leafSize, deficiencies) VALUES (?, ?, ?, ?, ?)', (plant, EC, height, leafSize, deficiencies))
        db.commit()
    elif plant<17:
        db.execute('INSERT INTO PH (PN, ph, EC, height, leafSize, deficiencies) VALUES (?, ?, ?, ?, ?, ?)', (plant, ph, EC, height, leafSize, deficiencies))
        db.commit()
    elif plant<25:
        db.execute('INSERT INTO CalMag (PN, CM, EC, height, leafSize, deficiencies) VALUES (?, ?, ?, ?, ?, ?)', (plant, CM, EC, height, leafSize, deficiencies))
        db.commit()
    else:
        db.execute('INSERT INTO LI (PN, EC, height, leafSize, deficiencies) VALUES (?, ?, ?, ?, ?)', (plant, EC, height, leafSize, deficiencies))
        db.commit()

    return render_template("logdatasuccess.html")
#---------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    serve(app,host = '0.0.0.0',port = 5000)
    #app.run(host='0.0.0.0')
    #app.run(debug=True,host='0.0.0.0')

