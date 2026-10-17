import unittest
from generate import classify,normalize
from game_arena.utils import get_match_result
class ClassificationTests(unittest.TestCase):
 def sample(self,loser=0,**extra):
  return dict(name0='LLM_test',name1='bot/001',done=False,winner=None,player_err_counts=[int(loser==0),int(loser==1)],**extra)
 def test_illegal_either_side_loses(self):
  for loser in [0,1]:
   d=self.sample(loser,exception='Invalid move_str: e2e4. legal move_strs: []')
   kind,idx=classify(d);self.assertEqual((kind,idx),('illegal_move',loser))
   self.assertEqual(get_match_result(normalize(d,kind,idx),False),('error',1-loser))
 def test_legacy_retry_evidence(self):
  d=self.sample(exception='Max retry count 3 reached.',exception_traceback='ValueError: Max retry count 3 reached for move: 2')
  self.assertEqual(classify(d),('illegal_move',0))
 def test_api_after_illegal_not_scored(self):
  d=self.sample(exception='Max retry count 3 reached.',exception_traceback='No response from model; earlier illegal retry')
  self.assertEqual(classify(d),('api_or_harness_failure',None))
 def test_bot_crash(self):
  self.assertEqual(classify(self.sample(1,exception="Policy raised an exception: KeyError: 'q'")),('bot_code_error',1))
 def test_io_not_forfeit(self):
  self.assertEqual(classify(self.sample(1,exception='[Errno 5] Input/output error')),('api_or_harness_failure',None))
 def test_completed(self):
  self.assertEqual(classify({'done':True}),('completed',None))
if __name__=='__main__':unittest.main()
