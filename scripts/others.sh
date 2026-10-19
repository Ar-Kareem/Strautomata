# find all folders with a specific name, in 'src/game_arena/' run:
# find . -type d -name 'mimo_v2_flash_free' -print
# find . -type d -name 'devstral_2512_free' -print

# ----------------------
# # rename all folders with a specific name, in 'src/game_arena/' run `../../scripts/others.sh`
# DRYRUN=1   # set to 0 to actually rename
# i=1
# find . -type d -name 'devstral_2512_free' -print0 | while IFS= read -r -d '' d; do
#   src="$d"
#   dst="${d%/devstral_2512_free}/devstral_2512"
#   if (( DRYRUN )); then
#     printf '%d: mv -- %q %q\n' "$i" "$src" "$dst"
#   else
#     mv -- "$src" "$dst"
#   fi
#   i=$((i+1))
# done

# ----------------------
python -m scripts.analyze_current_bots
