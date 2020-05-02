import csv, itertools, operator
from flask import *
from elo import elo, expected, elo_gain
app = Flask(__name__)

db_file="players.csv"
#db_file="test.csv"
db={}

def readdb():
    reader = csv.reader(open(db_file, 'r'))
    d = {}
    for row in reader:
        k, v = row
        db[k] = v

def savedb():
    with open(db_file, "w") as fd:
        for key, value in db.items():
            fd.write(key+','+value+'\n')

@app.before_first_request
def setup():
    readdb()


@app.route('/')
def index():
    sorted_db = sorted(db.items(), key=operator.itemgetter(1), reverse=True)
    return render_template('index.html', result = sorted_db)

@app.route('/addplayer')
def addplayer():
    return render_template('addplayer.html')

@app.route('/submitplayer', methods = ['POST'])
def submitplayer():
    if request.method == 'POST':
        name = request.form['name']
        #check name is not empty
        if not name:
            return redirect(url_for('error'))
        elo = request.form['elo']
        #check elo is a number
        if not elo.isnumeric():
            return redirect(url_for('error'))
        #save player in db
        db[str(name)] = elo
        savedb()
        return redirect(url_for('index'))

@app.route('/match')
def match():
    result = sorted(list(db.keys()), key=str.lower)
    return render_template('match.html', result = result)

def generate_groups(lst, n):
    if not lst:
        yield []
    else:
        for group in (((lst[0],) + xs) for xs in itertools.combinations(lst[1:], n-1)):
            for groups in generate_groups([x for x in lst if x not in group], n):
                yield [group] + groups

@app.route('/result', methods = ['POST'])
def result():
    players = {}
    if request.method == 'POST':
        for i in request.form:
            players[i] = db[i]
        if not len(players) % 2 == 0:
            return redirect(url_for('error'))
        team_size = len(players)/2
        #Find balanced match
        permut = list(generate_groups(players.keys(), team_size))
        #Calculate average elos
        best_elo = 99999
        best_match = {}
        for match in permut:
            team1_elo = 0
            team2_elo = 0
            for player in match[0]:
                team1_elo += int(db[player])
            for player in match[1]:
                team2_elo += int(db[player])
            elo_difference = abs(team1_elo - team2_elo)
            if elo_difference < best_elo:
                best_elo = elo_difference
                best_match = match
        return render_template('result.html', result=best_match, elo_diff = best_elo)

@app.route('/update', methods = ['POST'])
def update():
    if request.method == 'POST':
        #Update player elo according to result
        winners = request.form['winner'].split(',')
        loosers = request.form['looser'].split(',')
        winners_elo = 0
        loosers_elo = 0
        for player in winners:
            winners_elo += int(db[player])
        for player in loosers:
            loosers_elo += int(db[player])
        #You may want to flatten elo per player number
        #winners_elo = winners_elo / len(winners)
        #lossers_elo = loosers_elo / len(loosers)
        for player in winners:
            exp_score = expected(winners_elo, loosers_elo)
            elo = elo_gain(exp_score, 1)
            db[player] = str(int(db[player]) + int(round(elo)))
        for player in loosers:
            exp_score = expected(loosers_elo, winners_elo)
            elo = elo_gain(exp_score, 0)
            db[player] = str(int(db[player]) + int(round(elo)))
        savedb()
        return redirect(url_for('index'))

@app.route('/error')
def error():
    return render_template('error.html')

if __name__ == '__main__':
    app.run("0.0.0.0")
