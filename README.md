# Project's goal

 Given a chess game, the goal is to predict the elo rating of the players.

# Database

We use the games from <https://theweekinchess.com/twic>. That includes approximately 2.8 million games. These games are competition games that are played over the board (i. e. in person, not online).
We analyze them using Stockfish (<https://stockfishchess.org/>). Future plans is to perhaps use leela zero <https://lczero.org/>.
We have another database from <https://shop.chessok.com/index.php?main_page=index&cPath=7_54> of 5 million games, but those will not be analyzed. They may be used to study the openings.

# Methodology

1. We will try to find a relationship of Average CentiPawn Loss (ACPL) with the elo rating of players
2. We will classify the opening choices and the opening accuracy based on the elo rating of players
3. We will try to improve upon ACPL, constructing a function that better demonstrates the accuracy level of each game.

# KPI  

- accuracy of the elo estimator
- number of games needed to make an accurate guess

# Stakeholders

- Public: It could be made as an app and used for commercial use among chess players
- Chess platforms, either for commercial use ( to be used when a player is analyzing their game ) or to complement cheating detection algorithms
