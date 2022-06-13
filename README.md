
# Lasers, Inc.
A game for Vim, because why should Emacs have all the fun?

I was in the mood to play a game in my terminal the other day, only to realize
that all the fun games are inside Emacs. This project attempts to remedy this
horrific situation.

## Setup and usage
 - This game relies on Neovim and Python 3. Make sure the `pynvim` pip3 package
   is installed.
 - If the `playsound` pip3 package is installed, the game will play sound
   effects.
 - Clone this repo, `cd` into it, and then run `nvim -u LasersInc.nvim`.
 - The game will quickly register itself as a python plugin, using
   `:UpdateRemotePlugins`, and then start.

