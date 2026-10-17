import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse
import numpy as np
import pandas as pd
from src import data_pipeline as dp
from src.quality import reconcile, validate_teams
from src.features import attach_features, SKILLS
from src import features
from src.lineups import load_rows,consolidate_membership
from src.models import lineup_weights

def row():
    return {'EntityId':'1-2-3-4-5','TeamId':'10','Name':'fixture',
        'SecondsPlayed':60,'OffPoss':2,'DefPoss':2,'Points':3,'OpponentPoints':2,'PlusMinus':1}

class Integrity(unittest.TestCase):
    def test_reordered_membership_aggregates_counts(self):
        r=row();s=r|{'EntityId':'5-4-3-2-1','OffPoss':3,'Points':6,'PlusMinus':4}
        result=consolidate_membership(pd.DataFrame([r,s]))
        self.assertEqual(len(result),1)
        self.assertEqual(result.iloc[0].OffPoss,5)
        self.assertEqual(result.iloc[0].Points,9)
        self.assertEqual(result.iloc[0].EntityId,'1-2-3-4-5')
        with self.assertRaises(ValueError):consolidate_membership(pd.DataFrame([r,r]))

    def test_retained_representation_weights(self):
        d=pd.DataFrame({'lineup_key':['a','a','a','b','b'],'possessions':[120,120,120,200,200]})
        np.testing.assert_allclose(lineup_weights(d),[40,40,40,100,100])
        self.assertAlmostEqual(lineup_weights(d).sum(),320)
        self.assertAlmostEqual(lineup_weights(d,False).sum(),2)
        self.assertAlmostEqual(lineup_weights(d,False,'representation').sum(),5)

    def test_profile_lag_normalization_and_eligibility(self):
        rows=[]
        for i,minutes in enumerate([100,600,800,1000,1200]):
            rows.append({'EntityId':i+1,'Name':str(i),'SecondsPlayed':minutes*60,
                'OffPoss':1000,'DefPoss':1000,**{k:(i+1)**2+j for j,k in enumerate(features.EVENTS)}})
        with tempfile.TemporaryDirectory() as tmp,patch.object(features,'OUT',Path(tmp)),patch.object(features,'load_rows',return_value=rows):
            result=features.player_profiles(['2022-23'])
            self.assertEqual(set(result.player_id),{2,3,4,5})
            self.assertTrue(result.feature_season.eq('2021-22').all())
            np.testing.assert_allclose(result[SKILLS+['quality']].mean(),0,atol=1e-12)
            np.testing.assert_allclose(result[SKILLS+['quality']].std(ddof=0),1,atol=1e-12)
            r=rows[1];fgm=r['FG2M']+r['FG3M'];fga=r['FG2A']+r['FG3A']
            expected=(r['Points']+.4*fgm-.7*fga-.4*(r['FTA']-r['FtPoints'])+.7*r['OffRebounds']+.3*r['DefRebounds']+r['Steals']+.7*r['Assists']+.7*r['Blocks']-.4*r['Fouls']-r['Turnovers'])*36/600
            self.assertAlmostEqual(result.iloc[0].quality_gmsc36,expected)
            saved=(Path(tmp)/'player_profiles.csv').read_bytes()
            features.player_profiles(['2022-23'],minimum_minutes=800,write_output=False)
            self.assertEqual((Path(tmp)/'player_profiles.csv').read_bytes(),saved)
        with patch.object(features,'load_rows',return_value=rows+[rows[0]]):
            with self.assertRaisesRegex(ValueError,'one row per player'):
                features.player_profiles(['2022-23'])

    def test_reconciliation_all_fields(self):
        r=row();reconcile([r],r)
        for field in ['SecondsPlayed','OffPoss','DefPoss','Points','OpponentPoints']:
            with self.subTest(field=field),self.assertRaises(ValueError):
                reconcile([r],r|{field:r[field]+1})
        self.assertEqual(len(reconcile([r|{'PlusMinus':0}],r)),1)
        with self.assertRaises(ValueError):reconcile([r|{'OffPoss':np.inf}],r)

    def test_full_season(self):
        teams=[{'EntityId':i,'GamesPlayed':82} for i in range(30)]
        validate_teams(teams)
        for bad in [teams[:-1],teams[:-1]+[teams[0]],teams[:-1]+[{'EntityId':29,'GamesPlayed':81}]]:
            with self.assertRaises(ValueError):validate_teams(bad)

    def test_cache_checksum_and_url(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(dp,'RAW',Path(tmp)):
            path=Path(tmp)/'test.json';payload=b'{"multi_row_table_data": []}'
            path.write_bytes(payload)
            path.with_suffix('.meta.json').write_text(json.dumps({'url':'expected','sha256':hashlib.sha256(payload).hexdigest()}))
            self.assertEqual(dp.fetch('test','expected'),{'multi_row_table_data':[]})
            with self.assertRaises(ValueError):dp.fetch('test','wrong')
            path.write_bytes(b'{}')
            with self.assertRaises(ValueError):load_rows(path)

    def test_date_partition_disjoint_and_additive(self):
        calls=[]
        def fake(name,url,refresh=False):
            q=parse_qs(urlparse(url).query);a=q['FromDate'][0];b=q['ToDate'][0]
            calls.append((a,b))
            if a=='2022-10-01' and b=='2022-12-31':
                return {'multi_row_table_data':[row()]*500}
            return {'multi_row_table_data':[row()]}
        with tempfile.TemporaryDirectory() as tmp,patch.object(dp,'RAW',Path(tmp)),patch.object(dp,'totals',return_value=[row()]*500),patch.object(dp,'fetch',side_effect=fake):
            result=dp.complete_lineups('2022-23',10)
            self.assertEqual(len(result),1)
            self.assertEqual(result[0]['OffPoss'],6)
            self.assertEqual(calls,[('2022-10-01','2022-12-31'),('2022-10-01','2022-11-15'),('2022-11-16','2022-12-31'),('2023-01-01','2023-06-30')])
            self.assertTrue((Path(tmp)/'pbp_2022-23_Lineup_10_complete.meta.json').exists())

    def test_same_season_profile_rejected(self):
        profiles=pd.DataFrame([{'season':'2022-23','feature_season':'2022-23','quality':0,**dict.fromkeys(SKILLS,0)}])
        with self.assertRaisesRegex(ValueError,'lagged'):
            attach_features(pd.DataFrame(),profiles)

if __name__=='__main__':unittest.main()
