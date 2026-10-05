"""Build and execute focused companion notebooks from the offline analytical outputs."""
import json
import os
from pathlib import Path
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
from .data_pipeline import ROOT
os.environ.setdefault('JUPYTER_RUNTIME_DIR',str(ROOT/'.cache'/'jupyter'))
os.environ.setdefault('IPYTHONDIR',str(ROOT/'.cache'/'ipython'))

SETUP="""from pathlib import Path
import json
import pandas as pd
import numpy as np
from IPython.display import display, Image, Markdown
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src' / 'data_pipeline.py').exists())
DATA = ROOT / 'data' / 'processed'
import sys
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
pd.set_option('display.max_columns', 12)
"""

def execute_local(book):
    """Execute top-to-bottom with a fresh IPython namespace and capture rich outputs.

    Avoids requiring a TCP kernel broker in restricted desktop environments. The
    generated notebooks remain ordinary Jupyter notebooks and can be rerun there.
    """
    shell=InteractiveShell.instance()
    shell.reset(new_session=False)
    count=0
    for cell in book.cells:
        if cell.cell_type!='code':
            continue
        count+=1
        with capture_output() as captured:
            result=shell.run_cell(cell.source,store_history=False)
        if result.error_before_exec is not None:
            raise result.error_before_exec
        if result.error_in_exec is not None:
            raise result.error_in_exec
        cell.execution_count=count
        cell.outputs=[]
        if captured.stdout:
            cell.outputs.append(nbf.v4.new_output('stream',name='stdout',text=captured.stdout))
        if captured.stderr:
            cell.outputs.append(nbf.v4.new_output('stream',name='stderr',text=captured.stderr))
        for output in captured.outputs:
            cell.outputs.append(nbf.v4.new_output('display_data',data=output.data,metadata=output.metadata))
    book.metadata['execution_method']='Fresh local IPython namespace; sequential cells; captured rich output'

def build(name,headline,context,cells,takeaways):
    book=nbf.v4.new_notebook()
    book.metadata.kernelspec={'name':'python3','display_name':'Python 3','language':'python'}
    book.cells=[nbf.v4.new_markdown_cell(f'# {name[3:].replace("_"," ").title()}\n\n## tl;dr\n{headline}\n\n## Context & Methods\n{context}\n\n### Key Assumptions\nRegular-season PBP Stats aggregates; lagged profiles; observational comparisons. See [methodology](../docs/methodology_notes.md).'),
        nbf.v4.new_markdown_cell('## Data\nRun the cached pipeline and offline analysis before this notebook. No network requests are made here.'),nbf.v4.new_code_cell(SETUP),nbf.v4.new_markdown_cell('## Results')]
    for title,code in cells:
        book.cells.extend([nbf.v4.new_markdown_cell('### '+title),nbf.v4.new_code_cell(code)])
    book.cells.append(nbf.v4.new_markdown_cell('## Takeaways\n'+takeaways))
    nbf.validate(book)
    path=ROOT/'notebooks'/f'{name}.ipynb'
    nbf.write(book,path)
    execute_local(book)
    nbf.write(book,path)
    print(f'Executed {path.name}',flush=True)

def main():
    s=json.loads((ROOT/'docs'/'results_summary.json').read_text(encoding='utf-8'))
    build('01_data_feasibility',f"Retrieved {len(s['seasons'])} outcome seasons and {s['unique_lineups']:,} canonical lineups. Internal reconciliation is distinct from independent source validation.",
        'Compare sources before modeling. [Source recommendation](../docs/data_feasibility.md). [API documentation](https://api.pbpstats.com/docs).',[
        ('Source access tests',"display(pd.read_json(ROOT/'docs'/'access_probes.json')[['name','seconds']])"),
        ('Season coverage',"display(pd.read_csv(DATA/'season_summary.csv'))"),
        ('Team reconciliation',"audit=pd.read_csv(ROOT/'docs'/'coverage_audit.csv')\ncols=[c for c in audit if c.endswith('_difference')]\ndisplay(audit.groupby('season')[cols].agg(['min','max']))\ndisplay(audit.groupby('season').date_partitioned.sum().rename('capped_queries_recovered'))"),
        ('Validation evidence',"display(json.loads((ROOT/'docs'/'validation_summary.json').read_text()))\ndisplay(pd.read_csv(ROOT/'docs'/'quarantine.csv'))")],
        'The 500-row API cap required date partitioning. Preserve source conventions and caches. External NBA box-score reconciliation remains a research limitation.')
    build('02_exploratory_analysis',f"The 50-possession sample contains {s['primary_cores']:,} comparison cores after lagged-profile eligibility.",
        'A core must retain at least two fifth players after each filter. All exposure totals are calculated on unique lineup keys.',[
        ('Before and after feature eligibility',"display(pd.read_csv(DATA/'thresholds_before_profiles.csv'))\ndisplay(pd.read_csv(DATA/'thresholds_after_profiles.csv'))"),
        ('Exposure distribution',"display(Image(filename=str(ROOT/'figures'/'possession_distribution.png')))"),
        ('Threshold tradeoff',"display(Image(filename=str(ROOT/'figures'/'threshold_tradeoff.png')))"),
        ('Where comparison variation is available',"teams=pd.read_csv(DATA/'team_comparison_coverage.csv')\ndisplay(teams.groupby('season')[['cores','core_rows','lineups']].sum())\ndisplay(teams.sort_values('cores',ascending=False).head(10))"),
        ('Independent SQL audit',"import sqlite3\nwith sqlite3.connect(DATA/'analysis.sqlite') as conn:\n    display(pd.read_sql_query((ROOT/'sql'/'analysis_queries.sql').read_text(),conn))")],
        'Thresholds change the population being studied. A higher threshold reduces sampling noise but does not eliminate selection bias. Do not count expanded rows as independent observations.')
    build('03_skill_profiles',f"Built {s['eligible_player_profiles']:,} eligible lagged player-season profiles; defense is represented only by block activity.",
        'Seasonal standardized skills use at least 500 prior minutes. Shrunk three-point accuracy uses a fixed 100-attempt prior. Quality is prior Game Score/36.',[
        ('Feature timing and normalization',"profiles=pd.read_csv(DATA/'player_profiles.csv')\nfrom src.features import SKILLS\nassert ((profiles.season.str[:4].astype(int)-profiles.feature_season.str[:4].astype(int))==1).all()\ndisplay(profiles.groupby('season')[SKILLS+['quality']].mean().round(8))"),
        ('Recognizable player profiles',"names=['Stephen Curry','Nikola Jokić','Rudy Gobert','Draymond Green','Luka Dončić']\ndisplay(profiles[(profiles.name.isin(names)) & (profiles.season==profiles.season.max())][['name','feature_season','prior_minutes','quality']+SKILLS].round(2))"),
        ('Correlated measurements',"display(Image(filename=str(ROOT/'figures'/'skill_correlation.png')))"),
        ('Eligibility loss',"display(pd.read_csv(DATA/'feature_coverage.csv'))")],
        'Box-score skills reflect roles and teammates. Blocks do not measure defense comprehensively. Missing prior history is an exclusion, not an imputed average rookie.')
    build('04_lineup_construction',f"{s['unique_lineups']:,} five-player lineups expand to {s['all_core_fifth_rows']:,} core/fifth representations.",
        'IDs are numerically sorted, with team and season added to contextual keys. The same outcome is deliberately represented five ways.',[
        ('Validate original and expanded keys',"lineups=pd.read_csv(DATA/'lineups.csv')\ncores=pd.read_csv(DATA/'core_observations_unfiltered.csv')\nassert len(cores)==5*len(lineups)\nassert not lineups.lineup_key.duplicated().any()\nassert not cores.duplicated(['core_key','fifth_id']).any()\ndisplay(cores[['season','team','core_id','fifth_id','lineup_id','possessions']].head())"),
        ('Trace one real lineup',"key=lineups.sort_values('possessions',ascending=False).iloc[0].lineup_key\ndisplay(cores[cores.lineup_key==key][['core_id','fifth_id','lineup_name','possessions','net_rating']])"),
        ('Reconcile counts without duplication',"display(pd.DataFrame({'lineup_rows':[len(lineups)],'expanded_rows':[len(cores)],'lineup_exposure':[lineups.possessions.sum()],'expanded_exposure_divided_by_five':[cores.possessions.sum()/5]}))")],
        'Expansion enables same-core comparisons; it does not create new minutes or independent evidence. Regression weights divide exposure among retained representations.')
    build('05_complementarity_analysis',f"Primary-sample correlation between talent and gap closure is {s['talent_complementarity_correlation']:.3f}; distinct definitions need not be statistically independent.",
        'Core skills are four-player averages. Fill is the capped increase in the weakest below-average dimension when forming the five-player average.',[
        ('Deficiencies by core',"display(pd.read_csv(DATA/'deficiency_summary.csv'))"),
        ('Talent versus complementarity',"display(Image(filename=str(ROOT/'figures'/'talent_complementarity.png')))"),
        ('Example chosen without outcomes',"display(Image(filename=str(ROOT/'figures'/'core_example.png')))\ndisplay(pd.read_csv(DATA/'core_example.csv').round(3))"),
        ('Sanity checks for the formula',"from src.features import complementarity\ncore=np.array([[-1.,0,0,0,0],[1.,2,3,4,5]])\nfifth=np.array([[1.,0,0,0,0],[9.,9,9,9,9]])\nfill,_,_=complementarity(core,fifth)\nassert np.allclose(fill,[.4,0])\nprint('A -1 core and +1 fifth closes 0.4 units; an all-positive core has zero measured gap.')")],
        'This is an initial interpretable specification. Elite overall production does not ensure gap closure; a good role match does not establish a causal performance benefit.')
    build('06_modeling','Preliminary within-core estimates and held-out franchise contrasts are shown below. Read uncertainty and sensitivity before interpreting the hypothesis.',
        f'Possession-weighted linear regression; core fixed effects; lagged fifth quality and five skill main effects. {s["primary_clubs"]} franchise clusters in the primary sample; all lineup representations remain together in holdout validation.',[
        ('Primary and threshold estimates',"coef=pd.read_csv(DATA/'model_coefficients.csv')\nprimary=coef[(coef.term=='complementarity') & coef.weighted & coef.skill_controls]\ndisplay(primary[['threshold','coefficient','ci_low','ci_high','p_value','rows','cores','lineups','within_r2']].round(4))\ndisplay(Image(filename=str(ROOT/'figures'/'model_effects.png')))"),
        ('Full specification sensitivity',"display(coef[coef.term==coef.fit_column][['threshold','fit_column','weighted','skill_controls','coefficient','ci_low','ci_high','p_value']].round(4))"),
        ('Holdout contrasts',"cv=pd.read_csv(DATA/'heldout_club_validation.csv')\ndisplay(cv.groupby('model')[['squared_error_sum','weight_sum']].sum().assign(rmse=lambda x:np.sqrt(x.squared_error_sum/x.weight_sum)))\nprint('Test outcomes are demeaned within core only to score contrasts; this is not prospective absolute-rating prediction.')")],
        'An adjusted association does not show that replacing a player would cause improvement. Residual talent error, lineup selection, opponent strength, and defensive measurement remain limitations. Null estimates or weaker alternative specifications must remain visible.')

if __name__=='__main__':main()
