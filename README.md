# Guess the Elo

## Investigating Correlation Between Game Performance and Player Rating in Chess

Team: Dorian Soergel, Foivos Chnaras, Lang Song

## Background and Project Overview

 Our project, inspired by the popular chess YouTube series ["Guess the Elo"](https://www.youtube.com/playlist?list=PLBRObSmbZluRiGDWMKtOTJiLy3q0zIfd7) explores the relationship between game performance and player ratings in chess. [Elo](https://en.wikipedia.org/wiki/Elo_rating_system) is a widely used rating system that measures a player’s skill based on their game results. With increasing allegations of cheating in chess, often justified using game performance metrics, our work seeks to investigate the validity of such claims and explore the potential for developing predictive and anti-cheating tools.

## Our Goal

- Analyze the correlation between chess performance metrics and Elo ratings.
- Develop insights into whether single-game performance metrics can indicate cheating.
- Predict Elo ratings using performance metrics aggregated across multiple games.

## Stakeholders

- Chess platforms and organizations for anti-cheating insights.
- Developers and researchers interested in Elo prediction algorithms.
- The general chess community and enthusiasts for engagement and learning.

## Methodology

- Data Collection: Analyzed 1 million games from [The Week in Chess](https://theweekinchess.com/twic), with a focus on games around 2200 Elo.
- Game Processing: Used [Stockfish](https://stockfishchess.org/), a state-of-the-art chess engine, to compute centipawn loss and evaluate positions. Approximately 30k games were processed at depth 20 for higher accuracy.

## Metrics Development

- Replicated [Lichess.org](lichess.org)’s Accuracy score and analyzed its correlation with Elo.
- Developed custom metrics, including "Winning Chance Loss," which quantifies the severity of mistakes by evaluating changes in winning probability between moves.
- Classified errors into bins of 5% for nuanced analysis.

## Results

### Single Game Analysis

Showes weak correlation between performance metrics and Elo, questioning the reliability of using single-game metrics for cheating accusations.

### Multiple Game Analysis

Aggregated performance metrics across 10 games per player. Regression analysis revealed significantly stronger correlations, indicating that long-term patterns are better predictors of Elo.

### Sample Size Concerns

Despite starting with a large database, grouping games by player reduced the effective sample size to 20k, which limits the robustness of findings.

## Future Work

- Expand the database and analyze games at greater depths.
- Incorporate additional features, such as opening and endgame mistakes.
- Leverage deep learning to explore position complexity and refine predictive models.
- Develop a web application for Elo prediction, accessible to the general public.

## Conclusion

 While single-game metrics lack reliability in predicting Elo or detecting cheating, aggregated data across multiple games holds significant potential. With further research and advanced computational techniques, this work could contribute to fair play in chess and enhance the experience of chess enthusiasts worldwide.

## Example Run

For performance reasons, we will show an example on how to run the processing with only chess games analysed with a depth of 20.

- Analyse the Games using [Analyzing_Games](https://github.com/foivoshn/Guess-The-Elo/tree/main/Analyzing_games). This has already been done, the results are in [Analysed_Games](https://github.com/foivoshn/Guess-The-Elo/tree/main/Analyzed_games).
- Clean the games, removing games played by bots, pre-arranged draws and games with unknown result by running [data_analysis/Cleaning.ipynb](https://github.com/foivoshn/Guess-The-Elo/blob/main/data_analysis/Cleaning.ipynb)
- Concatenate all games in one big CSV file by running [data_analysis/combine_files.ipynb](https://github.com/foivoshn/Guess-The-Elo/blob/main/data_analysis/combine_files.ipynb)
- Get the WCL tables and the linear regression of it by running [data_analysis/Linear_Regression.ipynb](https://github.com/foivoshn/Guess-The-Elo/blob/main/data_analysis/Linear_Regression.ipynb)
- Reproduce the results of the platform [Lichess.org](lichess.org) by running [data_analysis/lichess.ipynb](https://github.com/foivoshn/Guess-The-Elo/blob/main/data_analysis/lichess.ipynb)
- Perform further linear regression with different predictors by running [data_analysis/elo_prediction_langsong.ipynb](https://github.com/foivoshn/Guess-The-Elo/blob/main/data_analysis/elo_prediction_langsong.ipynb)
- Perform Ramdom Forest regression by running [data_analysis/RandomForest.ipynb](https://github.com/foivoshn/Guess-The-Elo/blob/main/data_analysis/RandomForest.ipynb)


## Aknowledgements

- This project uses data from the [Lichess API](https://lichess.org/api)
- This project uses the [Stockfish Chess Engine](https://stockfishchess.org/)
- This project uses the [python-chess](https://python-chess.readthedocs.io/en/latest/)  Package