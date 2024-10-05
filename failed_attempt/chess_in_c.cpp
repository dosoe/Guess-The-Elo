#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <stdexcept>
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\benchmark.h" // You will need to include the Stockfish headers
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\bitboard.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\engine.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\evaluate.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\memory.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\misc.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\movegen.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\movepick.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\numa.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\perft.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\position.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\score.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\search.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\thread.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\thread_win32_osx.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\timeman.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\tt.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\tune.h"
#include  "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\types.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\uci.h"
#include "C:\\Users\\foivo\\Documents\\stockfish\\Stockfish\\src\\ucioption.h"

using namespace std;

void analyze_single_game(const string& pgn_file, const string& engine_path) {
    // Load the PGN file
    ifstream pgn(pgn_file);
    if (!pgn.is_open()) {
        cerr << "Could not open the PGN file." << endl;
        return;
    }

    // Initialize Stockfish engine
    Stockfish engine(engine_path);
    engine.start();

    string line;
    Board board; // Set up the initial board position
    cout << "Initial board position (FEN): " << board.fen() << endl;

    // Read the PGN headers
    while (getline(pgn, line)) {
        if (line.find("[WhiteElo") != string::npos) {
            cout << "White Elo: " << line << endl;
        } else if (line.find("[BlackElo") != string::npos) {
            cout << "Black Elo: " << line << endl;
        } else if (line.find("[Result") != string::npos) {
            cout << "Result: " << line << endl;
        } else if (line.empty()) {
            break; // End of headers
        }
    }

    int move_number = 1; // Track move number

    // Go through each move in PGN
    while (getline(pgn, line)) {
        istringstream move_stream(line);
        string san_move;

        // Process the move
        while (move_stream >> san_move) {
            try {
                Move move = board.parse_san(san_move); // Convert SAN to Move object
                cout << "Move " << move_number << ": " << san_move << endl;

                // Apply the move to the board
                board.push(move);
                
                // Get Stockfish evaluation
                auto eval_info = engine.analyse(board, Limit(0.1)); // Time limit in seconds
                auto eval = eval_info["score"].relative;

                string eval_value;
                if (eval.is_mate()) {
                    eval_value = "Mate in " + to_string(eval.mate());
                } else {
                    eval_value = to_string(eval.score() / 100.0); // Convert to centipawns
                }

                cout << "Evaluation after " << san_move << ": " << eval_value << endl;
                move_number++;

            } catch (const exception& e) {
                cout << "Error processing move " << san_move << ": " << e.what() << endl;
                cout << "Board FEN at error: " << board.fen() << endl; // Debug: Print FEN at the error point
                break; // Stop processing on error
            }
        }
    }

    engine.quit(); // Quit the engine
}

int main() {
    string stockfish_path = "C:\\Users\\foivo\\Downloads\\stockfish-windows-x86-64-avx2\\stockfish\\stockfish-windows-x86-64-avx2.exe"; // Path to the Stockfish engine
    string pgn_file = "example.pgn"; // The PGN file with your game

    // Analyze the single game
    analyze_single_game(pgn_file, stockfish_path);

    return 0;
}
