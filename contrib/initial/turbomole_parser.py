#! python
import sys
import os
import re
import math
import shutil


class turbomole_parser:
    """ parser turbomole force file """
    def __init__(self, config = {}):
        """
        init. variables
        """
        self.files = {'log': 'escf.out', 'info': 'info.dat'}
        self.freq = {}
        self.dim = {'n_atom': 28, 'n_mode': 78}
        self.par = {}
        self.results = {}
        print "hello world"
        if config != {}:
            self.files['log'] = config['log']
            self.files['newlog'] = config['newlog']
            self.dim['n_atom'] = config['n_atom']
            self.dim['n_mode'] = config['n_mode']
            # self.read_log()
            
        return


    def read_log_dim(self, i_traj = 1):
        """
        read number of atom in log file
        """        
        # total number of roots to be determined
        filename =  "./" + str(i_traj) + "/" + self.files['log']
        fp = open(filename, "r")
        pat_n_states = re.compile('total number of roots to be determined:[\s\t]+([0-9]+)')
        pat_n_atoms = re.compile('total:[\s\t]+([0-9]+)[\s\t]+([0-9]+)[\s\t]+([0-9]+)')

        for line in fp.readlines():
            m_n_states = pat_n_states.search(line)
            m_n_atoms = pat_n_atoms.search(line)
            if m_n_states is not None:
                n_state = m_n_states.group(1)
            if m_n_atoms is not None:
                n_atom = m_n_atoms.group(1)

        self.dim['n_state'] = int(n_state)
        self.dim['n_atom'] = int(n_atom)
        fp.close()
        
        return


    def __read_excitation_block(self, fp):
        """
        read in excitation info
        """
        pat = re.compile("[0-9]+[\s\t]+singlet a excitation")
        line = "not-empty-line"
        while line != "":
            line = fp.readline()
            m = pat.search(line)
            if m is not None:
                break
        n_lines = 75
        txt = []
        for i in xrange(n_lines):
            line = fp.readline()
            if line.strip() == "":
                continue
            txt.append(line)

        # excitation energy: line 2 3
        rec = txt[1].split(":")
        es_energy = float(rec[1])
        # eV
        rec = txt[2].split(":")
        es_energy_ev = float(rec[1])

        # os
        rec = txt[6].split(":")
        velocity = float(rec[1])
        rec = txt[7].split(":")
        length = float(rec[1])
        rec = txt[8].split(":")
        mix = float(rec[1])
        
        self.results['es_energy'].append(float(es_energy))
        self.results['es_energy_ev'].append(float(es_energy_ev))
        oscillator = {"velocity":velocity, "length": length, "mix": mix}
        self.results['oscillator'].append(oscillator)
            
        return


    def read_excitation_info(self, i_traj = 1):
        """
        read in all es info
        """
        n_state = self.dim['n_state']

        self.results['es_energy_ev'] = []
        self.results['es_energy'] = []       
        self.results['oscillator'] = []
        
        filename = "./" + str(i_traj) + "/" + self.files['log']
        fp = open(filename, "r")
        for i in xrange(n_state):
            self.__read_excitation_block(fp)
        fp.close()
        
        return
    
    def wrt_excitation_info(self, i_traj = 1):
        """
        wrt related excitation info.
        """
        results = self.results
        n_atom = self.dim['n_atom']
        n_state = self.dim['n_state']
        filename = "./" + str(i_traj) + "/" + self.files['info']
        file_out = open(filename, "w")
        print >>file_out, "# n_atom, n_state"
        print >>file_out, "%10d%10d" % (n_atom, n_state)
        # energy. eV
        es_energy_ev = results['es_energy_ev']
        print >>file_out, "# excitation energy (eV)"
        for ene in es_energy_ev:
            print >>file_out, "%15.8f" % ene

        oscillator = self.results['oscillator']
        print >>file_out, "# oscillator strength: length rep."
        for val in oscillator:
            print >>file_out, "%15.8f" % val['length']
        file_out.close()
        return

    def read_excitation_many(self):
        """
        read excitation in many files
        """
        line = raw_input("how many trajectory [default 1]: \n > ")
        rec = line.split()
        n_traj = int(rec[0])
        n_atom = self.dim['n_atom']
        n_state = self.dim['n_state']
        self.dim['n_traj'] = n_traj
        energy = []
        strength = []
        for i_traj in xrange(1, n_traj+1):
            self.read_excitation_info(i_traj)
            self.wrt_excitation_info(i_traj)
            
            for ene in self.results['es_energy']:
                energy.append(ene)
            for val in self.results['oscillator']:
                strength.append(val['length'])
        # write done into one file.
        filename = "excitation.dat"
        fp = open(filename, "w")
        print >>fp, "# n_traj n_state"
        print >>fp, "%10d%10d" % (n_traj, n_state)
        print >>fp, "# \Delta E; osciallator \rho=f/deltaE"
        for ene, length in zip(energy, strength):
            print >>fp, "%15.8f%15.8f%15.8f" % (ene, length, length/ene)
        fp.close()
        return

    def __read_turbo_log_geom(self):
        """ read gaussian geom data """
      
        filename = self.files['log']
        fp = open(filename, "r")
        n_atom = self.dim['n_atom']
        
        line = "EMPTY"
        pat = re.compile("Atomic coordinate, charge and isotop information")

        pos = 0 
        geom = [{} for i in xrange(n_atom)]
        while line != "":
            line = fp.readline()
            m = pat.search(line)
            if m is not None:
                pos = fp.tell()
                break

        # read geom
        if pos != 0:
            print "Find Geometry"
            fp.seek(pos)
        else:
            print "log file error. check ??"
            exit(1)
            
        # start to read geom
        # jump four lines  
        for i in xrange(4):
            line = fp.readline()
           # print line
        # read coord.
        for i in xrange(n_atom):
            coord = [0.0 for j in xrange(3)]
            line = fp.readline()
            record = line.split()
            atom_number = int(float(record[5]))
            atom_label= record[3]
            coord[0] = float(record[0])
            coord[1] = float(record[1])
            coord[2] = float(record[2])
            atom = {'atom_number': atom_number, 'atom_label': atom_label,
                    'coord': coord}
            geom[i] = atom        
 
        self.freq['geom'] = geom

        # dump xyz file for check
        file_xyz = open("check.xyz", "w")
        n_atom = self.dim['n_atom']
        print >>file_xyz, "%10d\n" % n_atom
        b2a = 0.529177
        for atom in geom:
            print >>file_xyz, "%10s%15.8f%15.8f%15.8f" % (atom['atom_label'],
                                                          atom['coord'][0]*b2a,
                                                          atom['coord'][1]*b2a,
                                                          atom['coord'][2]*b2a)
        file_xyz.close()
         
        fp.close()
        
        return

    def __read_turbo_log_freq_block(self, fp, i_block):
        """
        read in one block and assign variables
        """
        n_atom = self.dim['n_atom']
        n_col = 6
 
        line = fp.readline()

        pat_freq = re.compile("frequency")
        pat_mass = re.compile("reduced mass(g/mol)")
        pat_value = re.compile("RAMAN")
        while line != "":
            line = fp.readline()
            m1 = pat_freq.search(line)
            m2 = pat_mass.search(line)
            m3 = pat_value.search(line)

            if m1 is not None:
                record = line[20:].split()
                for f in record:
                    self.freq['freq'].append(float(f))             

            if m3 is not None:
                line = fp.readline()
                pos_value = fp.tell()
                break
 
        # read in normal modes       
        i_start = i_block * n_col 
        fp.seek(pos_value)

        for i in xrange(0, n_atom*3):
            line = fp.readline()
            record = line[20:].split()
            n_col_tmp = len(record)
            for j in xrange(i_start, i_start + n_col_tmp):
                j_col = j - i_start
                self.freq['normal_mode'][j][i] = float(record[j_col])
                
        #print self.freq['normal_mode'][0], self.freq['freq']
        # mass
        line = fp.readline()
        line = fp.readline()       
        record = line[20:].split()
        for mass in record:
            self.freq['mass'].append(float(mass))
                 
        return

 
    def __read_turbo_log_freq(self):
        """ read in every normal mode """
        filename = self.files['log']
        fp = open(filename, "r")
        pat1 = re.compile("NORMAL MODES and VIBRATIONAL FREQUENCIES")
        print "Begin to read frequency of each mode"
        line = "EMPTY"
        while line != "":
            line = fp.readline()
            m = pat1.search(line) 
            if m is not None:
                print "Find the normal modes"
                break
         # jump thirteen lines
        for i in xrange(13):  
            line = fp.readline()
 
        # read data now
        n_mode = self.dim['n_mode']
        n_atom = self.dim['n_atom']
        n_zero_mode = 3 * n_atom - n_mode
        n_col = 6
        n_block = n_natom*3/n_col+1 if n_atom*3%n_col>0 else n_atom*3/n_col
        
        # set dim. info.
        self.freq['n_mode'] = n_mode
        self.freq['n_atom'] = n_atom
        
        self.freq['mass'] = []
        self.freq['freq'] = []
        self.freq['normal_mode'] = [[0.0 for i in xrange(n_atom*3)] for j in xrange(n_atom*3)]
        self.freq['coor_vib'] = [[0.0 for i in xrange(n_atom*3)] for j in xrange(n_mode)]
        # read in
        for i in xrange(n_block):
            self.__read_turbo_log_freq_block(fp, i)
            
        self.freq['freq'] = self.freq['freq'][n_zero_mode:]
        self.freq['mass'] = self.freq['mass'][n_zero_mode:]
        self.freq['normal_mode'] = self.freq['normal_mode'][n_zero_mode:]
        # print self.freq['normal_mode'][70]
        # Write down the final transfermation matrix S(n_mode, n_atom)
        normal_mode = self.freq['normal_mode']
        mass_mode = self.freq['mass']
       
        for i in xrange(n_mode):
            for j in xrange(n_atom*3):                
                #print "%15.8f %15.8f" % (normal_mode[i][j],mass_mode[i])
                self.freq['coor_vib'][i][j] = normal_mode[i][j] / math.sqrt(mass_mode[i])

        fp.close()
        
        return

    def dump_turbo_log_freq(self):
        """
        write down freq related data in a specific format.
        """
        filename = self.files['newlog']
        fp = open(filename, "w")
        n_atom = self.freq['n_atom']
        n_mode = self.freq['n_mode']
        geom = self.freq['geom']
        print >>fp, "ATOMIC GEOMETRYS(AU)"
        # geometry
        print >>fp, "%10d" % (n_atom)
        for i in xrange(n_atom):
            atom = geom[i]
            print >>fp, "%5s%10d" % (atom['atom_label'], atom['atom_number']),
            for j in xrange(3):
                print >>fp, "%15.8f" % atom['coord'][j],
            print >>fp, ""
        # normal modes
        print >>fp, "%10d%10d" % (n_mode, n_atom)
        freq = self.freq['freq']
        mass = self.freq['mass']
        coor_vib = self.freq['coor_vib']
        print >>fp, "FREQUENCY(cm**-1)"
        for i in xrange(n_mode):
            print >>fp, "%15.8f" % (freq[i])
                   
        print >>fp, "REDUCED MASS(AMU)"        
        for i in xrange(n_mode):
            print >>fp, "%15.8f" % (mass[i])
 
        print >>fp, "NORMAL MODE"
        for i in xrange(n_mode):
            this_mode = coor_vib[i]
            for j in xrange(n_atom):
                print >>fp, "%15.8f%15.8f%15.8f" \
                % (this_mode[j*3+0], this_mode[j*3+1], this_mode[j*3+2])
        fp.close()
        
        return
    
    def read_log(self):
        """
        read gaussian log file
        """ 
        filename = self.files['log']
        file_out = open(filename, "r")
        
        # read gaussian geometry
        self.__read_turbo_log_dim()
        self.__read_turbo_log_geom()
        self.__read_turbo_log_freq()
        self.dump_turbo_log_freq()

        file_out.close()
        
        return
    
### main program
if __name__ == "__main__":
    turbo = turbomole_parser()
    turbo.read_log_dim(i_traj = 1)
    turbo.read_excitation_many()
    
    #turbo.read_excitation_info()
    #turbo.wrt_excitation_info()
 


    
