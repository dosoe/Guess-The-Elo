# Guess The Elo

Data Science project for the Erdos Institute Data Science Boot Camp Fall 2024

Foivos Chnaras, Dorian Soergel, Lang Song

## Project goal

Chess uses the [Elo rating system](https://en.wikipedia.org/wiki/Elo_rating_system) to calculate relative skill levels of players. The Elo system gives each player a score and the score difference gives the win probability of a player against another. After every game, the Elo of both players is adjusted, with the winner gaining points and the loser losing points.

One would thus expect the Elo of a player to depend on the way he plays. Our project aims to predict the Elo of a player given one or more games.

## Stakeholders

Cheating is an ever present threat in chess. Having a way to infer the Elo of a player from some of his games would provide a way to assess whether a player plays at a level consistent with their Elo and could thus be used to complement existing cheating detection algorithms.

Online chess platform, like any online game, have an interest in providing matchmaking that is as balanced as possible. Having a way to estimate the Elo of a new player after a few games would therefore be of interest to provide balanced games as quickly as possible.

Getting an approximate Elo estimation could also be of interest for individual players curious to assess their level.

## KPI  

The two metrics we focus for this project are:

- the accuracy of the elo estimator
- the number of games needed to make an accurate guess

## Database

We use the games from [The Week in Chess](https://theweekinchess.com/twic). That includes approximately 2.8 million games. These games are competition games that are played over the board (i. e. in person, not online).
We analyze them using [Stockfish](https://stockfishchess.org/). Future plans is to perhaps use [leela zero](https://lczero.org/).
We have another database from [chessok](https://shop.chessok.com/index.php?main_page=index&cPath=7_54) of 5 million games, but those will not be analyzed. They may be used to study the openings.

## Methodology

### Data Processing and Cleaning

1. We use the game analyser from [Stockfish](https://stockfishchess.org/) to get an evaluation of the successive position in each of our games. This is done [here](https://github.com/foivoshn/Guess-The-Elo/tree/main/Analyzing_games).
2. We clean the data, eliminating all pre-arranged games, games played by bots or games with no recorded outcome. This is done [here](https://github.com/foivoshn/Guess-The-Elo/blob/main/data_analysis/Cleaning.ipynb).
3. We calculate winning chance statistics for each position, to get a winning probability for each evaluation range. This has been done several times, using different training sets and once using the whole dataset, to check for differences. The differences being very small, we have decided to use the whole dataset, as it provides us with more flexibility to split the dataset in different ways later down the line. This is done [here](https://github.com/foivoshn/Guess-The-Elo/blob/main/data_analysis/winning_chances.ipynb)
4. For each move, using that winning probability, we calculate the decrease in winning probability (WCL, Winning Chance Loss) for each move, thus getting a quantitative metric of the quality of each move. This is done [here](https://github.com/foivoshn/Guess-The-Elo/blob/main/data_analysis/winning_chances.ipynb)

### Data Fitting

We chose two main routes to predict the Elo of a player:

- Either performing a fit directly on the WCL of each move. This has the advantage of using directly the WCL, but the downside of being tied to the number of moves: The fit needs to be done several times, once for each game length.
- Or by binning the WCL and counting the number of mistakes per game and their gravity. This has the downside of adding a step of processing, but it makes more sense in terms of chess and can be done directly on the whole dataset without the need to split by game length.

For the reasons listed above, we have decided to go with the latter.

In addition to the WCL, we also use the following features, all categorical: Game Result, Opening, Opening Variation and Color.
We did not use the Elo of the opponent, as most games are balanced and the Elo of the opponent is thus closely matched with the Elo of the player.

We perform a linear regression on these features, as well as a Random Forest Regressor. Both give similar root mean square error, but Random Forest tends to be more accurate on both ends of the Elo distribution.

We also classify the games by player and perform a regression using 10 games rather than one. The results show a spectacular improvement in fit.
