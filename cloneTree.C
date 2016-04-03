/*
  cloneTree.C

  Extract the nominal tree from your HistFitter inputs -- you can run on your laptop easily this way!
  This script is a bit dumb, but it was written very quickly and it does the job I need ... it's
  mostly provided as an example.

  MLB <matt.leblanc@cern.ch>
  Based on a script from Matt Gignac <matthew.gignac@cern.ch>

  Usage: root -l -b -q 'cloneTree.C("path/to/input.root","path/to/output.root")'
 */

void cloneTree(TString inFile, TString outFile)
{

  //TString inputTree ="allTrees.full.merge_v18.root";  
  TFile* in  = new TFile(inFile,"READ");

  if( !in->IsOpen() )
    {
      cout << "Error opening files! Exiting!" << endl;
      return;
    }
  
  TIter nextkey(in->GetListOfKeys());
  TKey *key;
  while ((key = (TKey*)nextkey()))
    {
      in->cd();
      TTree *tree = (TTree*)key->ReadObj();
      if(!tree)
	{
	  cout << "Could not read tree!" << endl;
	  continue;
	}

    TString oldTreeName = tree->GetName();
    //
    if(oldTreeName.Contains("nominal"))
      {
	cout << "Tree name: " << oldTreeName << endl;
	TFile* out = new TFile(outFile,"RECREATE");
	TTree* outTree = tree->CloneTree();
	outTree->SetDirectory(out);
	outTree->Write();
	out->Close();
      }
  }
  in->Close();
}
