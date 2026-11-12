"""No imported Dutch junction network; local circuit uses source-linked place cards."""
from config import BUILD

def main():
    (BUILD/'routes.json').write_text('{"nodes":[],"ways":[],"routes":[]}')
if __name__=='__main__':main()
