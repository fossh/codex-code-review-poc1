# Prospect Naming Rules

Please see below for some general guidelines on naming conventions. We should stick to these as far as possible going forward. For people reviewing others code, and when submitting code for review, please be cognisant of these.

If you are unsure about variable names, please reach out to @James Tozer, @Mark Einhorn or @Uday Patel.

At the start of any project, we should align on names and conventions, which should largely be guided by this document.

## General Rules

Wherever possible, we should use **snake_case**.

For project / repository names, these should be as broad as possible. So `football` is better than "football_analytics" or "football_data" or "wigan". Similarly, `sponsorship` is better than "project_advantage", and so on.

Where possible, you should have the data structure in the name of an object, e.g. `football_player_db` (a database of all football players), `cricket_competition_df` (a dataframe of cricket competitions), `rugby_union_shirt_number_dict` (a dictionary of shirt numbers in rugby).

Use `model` rather than "mod" for a model object (e.g. `post_match_exp_win_model` rather than "exp_win_mod").

Where possible, use full words for variable names. So `competition_season_id` is better than "comp_seas_key".

## Permitted Abbreviations

The following abbreviations are permitted for common mathematical phrases:

| Abbreviation | Meaning | Usage |
|--------------|---------|-------|
| `exp` | expected | Used when building a performance model that quantifies a probability within a match, e.g. "exp_points", "exp_tackles" |
| `pred` | predicted | Used when building a model that predicts anything else, e.g. "pred_new_users", "pred_annual_value" |
| `adj` | adjusted | |
| `prob` | probability | |
| `avg` | average | |
| `std` | standard deviation | |
| `pct` | percent or percentage | |
| `diff` | differential | |

## Standard Entity Names

For common variable and object names, we should use the following terms when referring to specific entities:

| Use This | Not This | Notes |
|----------|----------|-------|
| `sport` | | When referring to a sport as a whole, e.g. golf, rugby league |
| `format` | | For a variant of a sport, e.g. T20 cricket, rugby union 7s, matchplay in golf |
| `match` | fixture, game | "game" can be used as a specific entity within tennis |
| `competition` | league, tournament, series | |
| `season` | year, edition | |
| `table` | standings, ladder, pool | |
| `round` | stage, match_week | |
| `team` | club, side | When referring to a team in general |
| `squad` | | When referring to the players currently contracted to a team in a given competition in a given season |
| `player` | | |
| `official` | | Can be a referee, umpire, TMO |
| `staff` | | Can be a head coach, assistant coach, director of sport, etc |
| `event` | | When referring to a specific action in a game of football, rugby union, basketball etc |
| `period` | | NB "half" or "quarter" are types of period |
| `venue` | stadium, ground | |
| `country` | nation, nationality | |
| `region` | | e.g. Europe, southern hemisphere |
| `position` | | When referring to a specific role on the field, e.g. striker or flanker |
| `shirt_number` | | When referring to a "7" or a "9" |
| `result` | | When referring to the outcome of a match; use `result_type` as a string with "win", "tie", "draw", "loss", and `result` as a float ranging from 0, 0.5 and 1 |
| `differential` | margin | When referring to the difference between two teams on a given statistic, including the final score |
| `minutes` | mins | Have an underscore between the number and minutes, e.g. `per_90_minutes` rather than "p90mins" |
| `box_scores` | | When referring to any aggregation of event data across a period, e.g. number of kicks and rucks in a quarter of rugby |
| `x_coord`, `y_coord`, `z_coord` | x, y, z | |

## ID and Name Fields

Where appropriate, we want to have a `_name` and `_id` version of each field. So you have a `team_name` and `team_id`, `venue_name` and `venue_id`, etc.

`id` should be lower case (not "ID").

## Sport Names

When referring to sports, we should always use:

| Use This | Not This |
|----------|----------|
| `football` | soccer |
| `american_football` | NFL |
| `australian_rules_football` | AFL |
| `rugby_union` | rugby (when union specifically) |
| `rugby_league` | rugby (when league specifically) |

We should always distinguish between `rugby_union` and `rugby_league`.

## Sport-Specific Terms

We can have sport-specific event categories:

- **Cricket**: innings, overs, balls
- **Rugby**: possessions, phases
- **Tennis**: games, points, shots

## Data Source Identifiers

If we have different data sources within a sport, it is worth including those in the variable names. So Lionel Messi would have:

- `player_id_statsbomb`
- `player_id_transfermarkt`
- `player_id_wyscout`
- `player_id_football_manager`

Always spell out the name of the source - TM could be Ticketmaster or Transfermarkt, for example.

---

# Prospect Coding Rules

## Code Quality Levels

There are three "quality" levels that we should use when writing code at Prospect, which depend on the nature of the work that is being done.

### Notebook
This is appropriate for one-off consulting projects or pieces of performance analysis, in which we need to write some code in order to reach an answer for a client, but we are not guaranteed to use that code again for future work. Examples of this would be: the SOPC Olympic project, the Six Nations pricing project, and various ad hoc questions that the ECB ask in cricket.

### Dev Pipeline
This is appropriate for a project that is likely to have continued use in future, but does not necessarily need to have all the robustness checks that are required for a fully deployed product (e.g. unit tests). Examples of this would be: the early phases of the Fanatics project, the Tahaluf project, and the SportsDawg project.

### Prod Pipeline
This is appropriate for any project or product which relies on regular ingestion and interaction from ourselves and clients, and therefore needs to be fully deployed. Examples of this would be: the Ticketmaster pipeline, the Formula 1 pipeline, the football pipeline and the cricket pipeline.

The data science coding standards below apply equally to Dev Pipeline and Prod Pipeline - the only real difference between the two should be the degree of CI/CD work and unit testing around the core code. For Notebook projects, the requirements are less stringent, but it is still a good idea to follow these rules when possible.

## Project, Repository and Pipeline Names

When setting up a repository on GitHub, try to use a simple, broad and descriptive name, e.g. "football_analytics", "cricket_pipeline", "f1_performance_models". The general rule guidelines for this are:

- Start the repository name with the sport, primary customer or data source, e.g. `cricket_`, `football_wyscout_`, `fanatics_`, `ticketmaster_saracens_`.
- Then have a descriptive name which summarises the function of the repository, e.g. `_simulator`, `_analytics`, `_sales_model`, `_scraper`, `_ETL`.

There is some flexibility about how big a single repository should be: there are some very big ones with lots of pipelines (e.g. "football_analytics"), and some where these are broken into different repositories (e.g. "cricket_simulator", "cricket_utils", "cricket_ETL"). Use whatever approach you think is most appropriate for a particular product or project.

Likewise, try to use simple, descriptive and consistent names of pipelines within a project. E.g. in "football_analytics", we have "metric_change", "player_value_analysis", "transfermarkt_data_ingestion".

## Kedro Folder Structure

We use the following folder structure when saving data within a Kedro project:

| Folder | Purpose | Examples |
|--------|---------|----------|
| `01_raw` | Source data exactly as received, with no manual editing or preprocessing | XLSX or CSV files from clients, API dumps, other external datasets |
| `02_intermediate` | Temporary or work-in-progress datasets used during processing | Cleaned but not standardized tables, joined datasets that still require further shaping, outputs from early nodes that aren't final |
| `03_primary` | The "single source of truth" datasets after initial cleaning/validation, which are clean and used throughout the pipeline | A deduplicated customer table, a processed time series with gaps filled, an external dataset that has had errors removed |
| `04_feature` | Feature tables used for statistical modeling | Feature-engineered variables, encoded categorical features, aggregated features per entity (user, session, product) |
| `05_model_input` | Final dataframes or matrices that can be fed directly into a model | Train/test/validation splits, preprocessed arrays or tensors, input formats required by specific model frameworks |
| `06_models` | The actual model or model ensemble objects | |
| `07_model_output` | Files produced by the models | Dataframes of predictions and evaluation metrics |
| `08_reporting` | Outputs that are intended for humans to read, rather than code | Charts and plots, dashboards, PDFs |

## Coding Rules

1. **Follow Prospect naming rules** wherever possible (e.g. "matches" instead of "games", "competitions" instead of "tournaments", dataframe variables should have `_df` at the end).

2. **Keep an eye out for bad code smells** - avoiding duplicated code and hard-coded values, for example. [Here is a good list of things to look out for](https://refactoring.guru/refactoring/smells).

3. **Use Google docstring format**, making sure to use full sentences and tidy grammar.

4. **Functions should be modular and focused on doing one thing well.** As a guideline, aim to keep each function under 100 lines of code and comments (excluding docstrings). If it grows longer, break it into smaller functions or helpers.

5. **Functions should have descriptive names beginning with a verb.** A function which outputs a dataframe should be called something like `create_[TBC]_df`. A function which trains a model should be called something like `train_[TBC]_model`.

6. **A modelling pipeline should use a standard flow:**
   - First create a training dataframe (e.g. `create_[TBC]_train_df`)
   - Then train a model (e.g. `train_[TBC]_model`)
   - Evaluate the model (e.g. `evaluate_[TBC]_model`)
   - Create predictions from the model (e.g. `create_[TBC]_predictions_df`)

7. **Helper functions should have an underscore at the start of their names.** If a helper function is used in multiple pipelines within a project, it should be in a dedicated `helper_functions/nodes.py` file or utils file. If a helper function is used in multiple projects, it should be in the Prospect package.

8. **Try to have at least one comment above every block of code**, explaining WHY more than HOW. The comments should be capitalised at the start and use tidy grammar.

9. **If the use of a function runs over multiple lines, use hanging indentation.** This means that there is no argument on the first line, each argument sits on a separate line, and the closing bracket is on a separate line. (This is to make the code less dependent on spacing if the names of variables or functions change.)

10. **As much as possible, use the `parameters.yml` files to contain lists / dictionaries of variables.** This will also help keep functions shorter.

11. **For objects (dataframes, lists, dictionaries), try to include the type of the object in the variable name**, e.g. `match_results_df`, `team_id_dict`, `competition_name_list`.
