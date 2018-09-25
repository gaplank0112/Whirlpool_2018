import sys
import sim_server
from utilities import str_datetime
import InitializeBusinessHours
import InitializeQueuePrioritization
sys.path.append("C:\Python26\SCG_64\Lib")


low, med, high = 2, 5, 8
debug_obj = sim_server.Debug()
model_obj = sim_server.Model()

def main():
    sim_server.Debug().trace(2,'-'*30)
    sim_server.Debug().trace(2,'Initialize Model called at ' + sim_server.NowAsString())

    model_obj.setcustomattribute('ScriptProfiles', {})
    InitializeBusinessHours.main()
    InitializeQueuePrioritization.main()

if __name__ == "__main__":
    main()
