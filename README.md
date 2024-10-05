# Project's goal: 
 Given a list of chess games of a player, the goal is to predict their elo rating. 

# Database: 
As a start, we'll be using the games found in https://theweekinchess.com/twic.
We will analyze them using Stockfish (https://stockfishchess.org/). Future plans is to perhaps use leela zero https://lczero.org/ 

# Methodology: 
1. We will try to find a relationship of Average CentiPawn Loss (ACPL) with the elo rating of players
2. We will classify the opening choices and the opening accuracy based on the elo rating of players
3. We will try to improve upon ACPL, constructing a function that better demonstrates the accuracy level of each game. 

# KPI:  
- accuracy of the elo estimator
- number of games needed to make an accurate guess

# Stakeholders:
- Public: It could be made as an app and used for commercial use among chess players
- Chess platforms, either for commercial use ( to be used when a player is analyzing their game ) or to complement cheating detection algorithms