"""No Dutch historical tour. Source-linked Saiwai cards provide the local circuit."""
from config import BUILD

def main():
    (BUILD/'history.json').write_text('{"stops":[]}')
if __name__=='__main__':main()
