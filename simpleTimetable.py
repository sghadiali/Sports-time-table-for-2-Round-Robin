#!/usr/bin/env python
# coding: utf-8
from ortools.linear_solver import pywraplp
from collections import defaultdict
import xml.dom.minidom
import time
import sys
start_time = time.perf_counter()
fileName = sys.argv[1]
doc = xml.dom.minidom.parse(fileName)

teams = doc.getElementsByTagName("Teams")[0]
numTeams = teams.getElementsByTagName("team").length
numSlots = 2*(numTeams - 1)
halfSlot = numSlots//2
boolPhase = False

Structure = doc.getElementsByTagName("Structure")
if (Structure[0].getElementsByTagName("gameMode")[0].firstChild.data == 'P'):
    boolPhase = True

X = {}
H = {}

solver = pywraplp.Solver('simple_mip_program', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
for i in range(numTeams):
    for j in range(numTeams):
        for s in range(numSlots):
            X[i,j,s] = solver.IntVar(0,1,'X[{0}][{1}][{2}]'.format(s,j,i))

for i in range(numTeams):
    for j in range(numTeams):
        for s in range(numSlots):
            for h in range(2):
                H[i,j,s,h] = solver.IntVar(0,1,'H[{0}][{1}][{2}][{3}]'.format(h,s,j,i))



# # **phase**
# ### A pair of team can not repeat their game in other slots in one phase
if (boolPhase):
    for i in range(numTeams):
        for j in range(numTeams):
            if i != j:
                solver.Add(solver.Sum([X[i,j,s] for s in range(halfSlot)])==1)
                solver.Add(solver.Sum([X[i,j,s] for s in range(halfSlot,numSlots)])==1)


# ### A Team can not play with itself
for s in range(numSlots):
    for i in range(numTeams):
        solver.Add(X[i,i,s]==0)


# ### In 1 slot, Total matches should be numTeams
# ### in 1 slot, Each teams can play with other teams only once

for s in range(numSlots):
    solver.Add(solver.Sum([X[i,j,s] for i in range(numTeams) for j in range(numTeams)])==numTeams)
    for i in range(numTeams):
        solver.Add(solver.Sum([X[i,j,s] for j in range(numTeams)]) == 1)
    for j in range(numTeams):
        solver.Add(solver.Sum([X[i,j,s] for i in range(numTeams)]) == 1)


# Total 48 Constraints
# ## Symmetry in $X_{ijs}$

for i in range(numTeams):
    for j in range(numTeams):
        for s in range(numSlots):
            solver.Add(X[i,j,s]==X[j,i,s])


# ## Introduction of Home Away Variable in $H_{ijsh}$

for i in range(numTeams):
    for j in range(numTeams):
        for s in range(numSlots):
            solver.Add(X[i,j,s]==H[i,j,s,0]+H[i,j,s,1])
            solver.Add(H[i,j,s,0]==H[j,i,s,1])
            solver.Add(H[i,j,s,1]==H[j,i,s,0])


# ## Home-Away constraint. A team Should Play with j in both Home and Away state 

for i in range(numTeams):
    for j in range(numTeams):
        solver.Add(solver.Sum([H[i,j,s1,1] for s1 in range(numSlots)])==solver.Sum([H[i,j,s2,0] for s2 in range(numSlots)]))
        if i != j:
            solver.Add(solver.Sum([H[i,j,s1,1] for s1 in range(numSlots)])==1)
            solver.Add(solver.Sum([H[i,j,s1,0] for s1 in range(numSlots)])==1)


# ## introduction of $home_{is}$ and $away_{is}$ variable for $i^{th}$ Team playing Home/Away in Slot $s$
# ## introduction of $breakHome_{is}$ and $breakAway_{is}$variable for $i^{th}$ Team playing Home/Away break in Slot $s$

home = {}
away = {}
breakHome = {}
breakAway = {}
for i in range(numTeams):
    for s in range(numSlots):
        home[i,s] = solver.IntVar(0,1,'home[{0}][{1}]'.format(s,i))
        breakHome[i,s] = solver.IntVar(0,1,'breakHome[{0}][{1}]'.format(s,i))        
        away[i,s] = solver.IntVar(0,1,'away[{0}][{1}]'.format(s,i))
        breakAway[i,s] = solver.IntVar(0,1,'breakAway[{0}][{1}]'.format(s,i))
        
for i in range(numTeams):
    for s in range(numSlots):
        for j in range(numTeams):
            solver.Add(home[i,s] >= H[i,j,s,0])
            solver.Add(away[i,s] >= H[i,j,s,1]) 
for i in range(numTeams):
    for s in range(numSlots):
        solver.Add(home[i,s] <= solver.Sum([H[i,j,s,0] for j in range(numTeams)]))
        solver.Add(away[i,s] <= solver.Sum([H[i,j,s,1] for j in range(numTeams)]))
for i in range(numTeams):
    for s in range(1,numSlots):
        solver.Add(breakHome[i,s] <= home[i,s])
        solver.Add(breakHome[i,s] <= home[i,s-1])
        solver.Add(breakHome[i,s] >= home[i,s] + home[i,s-1] - 1)
        solver.Add(breakAway[i,s] <= away[i,s])
        solver.Add(breakAway[i,s] <= away[i,s-1])
        solver.Add(breakAway[i,s] >= away[i,s] + away[i,s-1] - 1)


# ## Introduction of $y_{ijs_{1}s_{2}}$ which says whether Team $i$ and Team $j$ played in slot $s_{1}$ the first time and in slot $s_{2}$ the second time

# In[17]:


y = {}
if (not boolPhase):
    for i in range(numTeams):
        for j in range(numTeams):
            for s1 in range(numSlots):
                for s2 in range(s1,numSlots):
                    if s1 != s2:
                        y[i,j,s1,s2] = solver.IntVar(0,1,'y[{0}][{1}][{2}][{3}]'.format(s2,s1,j,i))
    for i in range(numTeams):
        for j in range(numTeams):
            for s1 in range(numSlots):
                for s2 in range(s1,numSlots):
                    if s1 != s2:
                        solver.Add(y[i,j,s1,s2] <= X[i,j,s1])
                        solver.Add(y[i,j,s1,s2] <= X[i,j,s2])            
                        solver.Add(y[i,j,s1,s2] >= X[i,j,s1]+X[i,j,s2]-1)            
else:
    for i in range(numTeams):
        for j in range(numTeams):
            for s1 in range(halfSlot):
                for s2 in range(halfSlot,numSlots):
                    if s1 != s2:
                        y[i,j,s1,s2] = solver.IntVar(0,1,'y[{0}][{1}][{2}][{3}]'.format(s2,s1,j,i))
    for i in range(numTeams):
        for j in range(numTeams):
            for s1 in range(halfSlot):
                for s2 in range(halfSlot,numSlots):
                    if s1 != s2:
                        solver.Add(y[i,j,s1,s2] <= X[i,j,s1])
                        solver.Add(y[i,j,s1,s2] <= X[i,j,s2])            
                        solver.Add(y[i,j,s1,s2] >= X[i,j,s1]+X[i,j,s2]-1)


constraints = doc.getElementsByTagName("Constraints")[0]
objective = solver.Objective()

CapacityConstraints = constraints.getElementsByTagName("CapacityConstraints")[0]


# ## CA1


CA1_constraints =  CapacityConstraints.getElementsByTagName("CA1")

D_CA1 = {}
for i,constraintsSet in enumerate(CA1_constraints):
    team_a = int(constraintsSet.getAttribute("teams"))
    D_CA1[i,team_a] = solver.NumVar(0,solver.infinity(),'D_CA1[{0}][{1}]'.format(team_a,i)) 

    max_ = int(constraintsSet.getAttribute("max"))
    min_ = int(constraintsSet.getAttribute("min"))
    mode_ = constraintsSet.getAttribute("mode")
    penalty_ = int(constraintsSet.getAttribute("penalty"))
    slots_ = constraintsSet.getAttribute("slots").split(';')    
    type_ = constraintsSet.getAttribute("type")
    
    if (mode_ == 'H'):
        mod = 0
    else:
        mod = 1
    if (type_ == "HARD"):
        solver.Add(min_ <= solver.Sum([H[team_a,j,int(slot),mod] for j in range(numTeams) for slot in slots_]))
        solver.Add(solver.Sum([H[team_a,j,int(slot),mod] for j in range(numTeams) for slot in slots_]) <= max_)
    else:
        solver.Add(D_CA1[i,team_a] >= min_ - solver.Sum([H[team_a,j,int(slot),mod] for j in range(numTeams) for slot in slots_]))
        solver.Add(D_CA1[i,team_a] >= solver.Sum([H[team_a,j,int(slot),mod] for j in range(numTeams) for slot in slots_]) - max_)
        objective.SetCoefficient(D_CA1[i,team_a],penalty_)


# ## CA2

CA2_constraints =  CapacityConstraints.getElementsByTagName("CA2")
D_CA2 = {}
for i,constraintsSet in enumerate(CA2_constraints):
    team_1 = int(constraintsSet.getAttribute("teams1"))
    slots_ = constraintsSet.getAttribute("slots").split(';')
    D_CA2[i,team_1] = solver.NumVar(0,solver.infinity(),'D_CA2[{0}][{1}]'.format(team_1,i)) 

    max_ = int(constraintsSet.getAttribute("max"))
    min_ = int(constraintsSet.getAttribute("min"))
    mode_ = constraintsSet.getAttribute("mode1")
    penalty_ = int(constraintsSet.getAttribute("penalty"))
    
    team_2 = constraintsSet.getAttribute("teams2").split(';')
    type_ = constraintsSet.getAttribute("type")
    if (mode_ == 'H'):
        mod = [0]
    elif(mode_ == 'A'):
        mod = [1]
    else:
        mod = [0,1]

    solver.Add(D_CA2[i,team_1] >= min_ - solver.Sum([H[team_1,int(j),int(slot),m] for j in team_2 for slot in slots_ for m in mod]))
    solver.Add(D_CA2[i,team_1] >= solver.Sum([H[team_1,int(j),int(slot),m] for j in team_2 for slot in slots_ for m in mod]) - max_)
    if (type_ == "HARD"):
        solver.Add(D_CA2[i,team_1]==0)
    else:
        objective.SetCoefficient(D_CA2[i,team_1],penalty_)

# ## CA3

D_CA3 = {} 
CA3_constraints = CapacityConstraints.getElementsByTagName("CA3")
for i,constraintsSet in enumerate(CA3_constraints):
    intp = int(constraintsSet.getAttribute("intp"))
    team_1 = (constraintsSet.getAttribute("teams1")).split(';')
    k_max = int(constraintsSet.getAttribute("max"))
    k_min = int(constraintsSet.getAttribute("min"))
    mode_1 = constraintsSet.getAttribute("mode1")
    penalty_ = int(constraintsSet.getAttribute("penalty"))
     
    team_2 = (constraintsSet.getAttribute("teams2")).split(';')
    type_ = constraintsSet.getAttribute("type")
    if mode_1 == 'H':
        mod = [0]
    elif mode_1 == 'A':
        mod = [1]
    else:
        mod = [0,1]
       
    for l in range(numSlots - intp + 1):
        for t in team_1:
            t = int(t) 
            D_CA3[i,l,t] = solver.NumVar(0,solver.infinity(),'D_CA3[{0}][{1}][{2}]'.format(t,l,i))
            if (type_ == "HARD"):
                solver.Add(k_min<=solver.Sum([H[t,int(j),s,m] for j in team_2 for s in range(l,l+intp) for m in mod]))            
                solver.Add(solver.Sum([H[t,int(j),s,m] for j in team_2 for s in range(l,l+intp) for m in mod]) <= k_max)
            else:
                solver.Add(D_CA3[i,l,t] >= k_min - solver.Sum([H[t,int(j),s,m] for j in team_2 for s in range(l,l+intp) for m in mod]))            
                solver.Add(D_CA3[i,l,t] >= solver.Sum([H[t,int(j),s,m] for j in team_2 for s in range(l,l+intp) for m in mod]) - k_max)
                objective.SetCoefficient(D_CA3[i,l,t],penalty_)

# ## CA4

CA4_constraints =  CapacityConstraints.getElementsByTagName("CA4")
D_CA4 = {}
for l,constraintsSet in enumerate(CA4_constraints):
    D_CA4[l] = solver.NumVar(0,solver.infinity(),'D_CA4[{0}]'.format(l))
    max_ = int(constraintsSet.getAttribute("max"))
    min_ = int(constraintsSet.getAttribute("min"))
    mode_ = constraintsSet.getAttribute("mode1")
    mode2 = constraintsSet.getAttribute("mode2")
    penalty_ = int(constraintsSet.getAttribute("penalty"))
    slots_ = constraintsSet.getAttribute("slots").split(';')
    team_1 = constraintsSet.getAttribute("teams1").split(';')
    team_2 = constraintsSet.getAttribute("teams2").split(';')
    type_ = constraintsSet.getAttribute("type")
    if (mode_ == 'H'):
        mod = [0]
    elif(mode_ == 'A'):
        mod = [1]
    else:
        mod = [0,1]
    if (type_ == "HARD"):
        if mode2 == "GLOBAL":
            solver.Add(min_ <= solver.Sum([H[int(i),int(j),int(slot),m].solution_value() for i in team_1 for j in team_2 for m in mod for slot in slots_]))
            solver.Add(solver.Sum([H[int(i),int(j),int(slot),m].solution_value() for i in team_1 for j in team_2 for m in mod for slot in slots_]) <=  max_)
        else:
            for slot in slots_:
                solver.Add(min_ <= solver.Sum([H[int(i),int(j),int(slot),m] for i in team_1 for j in team_2 for m in mod]))
                solver.Add(solver.Sum([H[int(i),int(j),int(slot),m] for i in team_1 for j in team_2 for m in mod]) <= max_)
    else:
        if mode2 == "GLOBAL":
            solver.Add(D_CA4[l] >= min_ - solver.Sum([H[int(i),int(j),int(slot),m] for i in team_1 for j in team_2 for slot in slots_ for m in mod]))
            solver.Add(D_CA4[l] >= solver.Sum([H[int(i),int(j),int(slot),m] for i in team_1 for j in team_2 for slot in slots_ for m in mod]) - max_)
        else:
            for slot in slots_:
                solver.Add(D_CA4[l] >= min_ - solver.Sum([H[int(i),int(j),int(slot),m] for i in team_1 for j in team_2 for m in mod]))
                solver.Add(D_CA4[l] >= solver.Sum([H[int(i),int(j),int(slot),m] for i in team_1 for j in team_2 for m in mod]) - max_)

        objective.SetCoefficient(D_CA4[l],penalty_)

# ## GA1

D_GA1 = {}
GameConstraints = constraints.getElementsByTagName("GameConstraints")[0]
GA1_constraints = GameConstraints.getElementsByTagName("GA1")

for i,constraint_set in enumerate(GA1_constraints):    
    Groups = constraint_set.getAttribute("meetings").split(';')
    D_GA1[i] = solver.NumVar(0,solver.infinity(),'D_GA1[{0}]'.format(i))
    Groups.pop()
    meeting_list = [0]*len(Groups)
    for g,group in enumerate(Groups):
        groupSplit = group.split(',')
        meeting_list[g] = [int(groupSplit[0]),int(groupSplit[1])]
    
    k_max = int(constraint_set.getAttribute("max"))
    k_min = int(constraint_set.getAttribute("min"))
    penalty_ = int(constraint_set.getAttribute("penalty"))
    type_ = constraint_set.getAttribute("type")
    slots_ = constraint_set.getAttribute("slots").split(';')
    solver.Add(D_GA1[i] >= k_min - solver.Sum([H[meeting[0],meeting[1],int(s),0] for meeting in meeting_list for s in slots_]))
    solver.Add(D_GA1[i] >= solver.Sum([H[meeting[0],meeting[1],int(s),0] for meeting in meeting_list for s in slots_]) - k_max)
    if (type_ == "HARD"):
        solver.Add(D_GA1[i] == 0)
    else:
        objective.SetCoefficient(D_GA1[i],penalty_)
                

# ## BR1

BreakConstraints = constraints.getElementsByTagName("BreakConstraints")[0]
D_BR1 = {}
BR1_constraints = BreakConstraints.getElementsByTagName("BR1")
for i,BR1_constraint in enumerate(BR1_constraints):
    slots_BR1 = BR1_constraint.getAttribute("slots").split(';')
    D_BR1[i] = solver.NumVar(0,solver.infinity(),'D_BR1[{0}]'.format(i))
    intp = int(BR1_constraint.getAttribute("intp"))
    mode_is_EQ = BR1_constraint.getAttribute("mode1")
    isHorA = BR1_constraint.getAttribute("mode2")
    penalty_BR1 = int(BR1_constraint.getAttribute("penalty"))    
    team_BR1 = BR1_constraint.getAttribute("teams")
    type_ = BR1_constraint.getAttribute("type")
    objective.SetCoefficient(D_BR1[i],penalty_BR1)
    if isHorA == 'HA':
        if mode_is_EQ == "LEQ":
            solver.Add(D_BR1[i] >= solver.Sum([(breakHome[int(team_BR1),int(s)]+breakAway[int(team_BR1),int(s)]) for s in slots_BR1]) - intp)
        else:
            solver.Add(D_BR1[i] >= solver.Sum([(breakHome[int(team_BR1),int(s)]+breakAway[int(team_BR1),int(s)]) for s in slots_BR1]) - intp)
            solver.Add(D_BR1[i] >= intp - solver.Sum([(breakHome[int(team_BR1),int(s)]+breakAway[int(team_BR1),int(s)]) for s in slots_BR1]))
    elif isHorA == 'H':
        if mode_is_EQ == "LEQ":
            solver.Add(D_BR1[i] >= solver.Sum([breakHome[int(team_BR1),int(s)] for s in slots_BR1]) - intp)
        else:
            solver.Add(D_BR1[i] >= solver.Sum([breakHome[int(team_BR1),int(s)] for s in slots_BR1]) - intp)
            solver.Add(D_BR1[i] >= intp - solver.Sum([breakHome[int(team_BR1),int(s)] for s in slots_BR1]))
    else:
        if mode_is_EQ == "LEQ":
            solver.Add(D_BR1[i] >= solver.Sum([breakAway[int(team_BR1),int(s)] for s in slots_BR1]) - intp)
        else:
            solver.Add(D_BR1[i] >= solver.Sum([breakAway[int(team_BR1),int(s)] for s in slots_BR1]) - intp)
            solver.Add(D_BR1[i] >= intp - solver.Sum([breakAway[int(team_BR1),int(s)] for s in slots_BR1]))
    if (type_ == "HARD"):
        solver.Add(D_BR1[i] == 0)
    else:
        objective.SetCoefficient(D_BR1[i],penalty_BR1)


# ## BR2

BreakConstraints = constraints.getElementsByTagName("BreakConstraints")[0]
BR2_constraints = BreakConstraints.getElementsByTagName("BR2")
D_BR2 = {}
for i,BR2_constraint in enumerate(BR2_constraints):
    D_BR2[i] = solver.NumVar(0,solver.infinity(),'D_BR2[{0}]'.format(i))
    intp = int(BR2_constraint.getAttribute("intp"))
    mode_is_EQ = BR2_constraint.getAttribute("mode2")
    type_ = BR2_constraint.getAttribute("type")
    penalty_BR2 = int(BR2_constraint.getAttribute("penalty"))
    

    solver.Add(solver.Sum([(breakHome[i,s]+breakAway[i,s]) for i in range(numTeams) for s in range(numSlots)]) <= D_BR2[i] + intp)
    if type_ == "HARD":
        solver.Add(D_BR2[i] == 0)
    else:
        objective.SetCoefficient(D_BR2[i],penalty_BR2)


# ## SE1
# Seperated by K time slots.

D_SE1 = {}
prod_SE1 = {}
SeparationConstraints = constraints.getElementsByTagName("SeparationConstraints")[0]
SE1_constraints = SeparationConstraints.getElementsByTagName("SE1")

if (boolPhase):
    for l,SE1_constraint in enumerate(SE1_constraints):
        k_min_se1 = int(SE1_constraint.getAttribute("min"))
        penalty_se1 = int(SE1_constraint.getAttribute("penalty"))
        type_ = SE1_constraint.getAttribute("type")
        for s1 in range(halfSlot):
            for s2 in range(halfSlot,numSlots):
                if s1 != s2:
                    D_SE1[l,s1,s2] = solver.NumVar(0,k_min_se1,'D_SE1[{0}][{1}][{2}]'.format(s2,s1,l))
                    solver.Add(D_SE1[l,s1,s2] >= k_min_se1 - s2 + s1)

        for i in range(numTeams):
            for j in range(numTeams):
                for s1 in range(halfSlot):
                    for s2 in range(halfSlot,numSlots):
                        if s1 != s2:
                            prod_SE1[l,i,j,s1,s2] = solver.NumVar(0,k_min_se1,'prod_SE1[{0}][{1}][{2}][{3}][{4}]'.format(s2,s1,j,i,l))
                            solver.Add(prod_SE1[l,i,j,s1,s2]<=k_min_se1*y[i,j,s1,s2])
                            solver.Add(prod_SE1[l,i,j,s1,s2]<=D_SE1[l,s1,s2])
                            solver.Add(prod_SE1[l,i,j,s1,s2] >=D_SE1[l,s1,s2]-k_min_se1*(1-y[i,j,s1,s2]))
                            if type_ == "HARD":
                                solver.Add(prod_SE1[l,i,j,s1,s2]==0)
                            else: 
                                objective.SetCoefficient(prod_SE1[l,i,j,s1,s2],penalty_se1)
else:
    for l,SE1_constraint in enumerate(SE1_constraints):
        k_min_se1 = int(SE1_constraint.getAttribute("min"))
        penalty_se1 = int(SE1_constraint.getAttribute("penalty"))
        type_ = SE1_constraint.getAttribute("type")
        for s1 in range(numSlots):
            for s2 in range(s1,numSlots):
                if s1 != s2:
                    D_SE1[l,s1,s2] = solver.NumVar(0,k_min_se1,'D_SE1[{0}][{1}][{2}]'.format(s2,s1,l))
                    solver.Add(D_SE1[l,s1,s2] >= k_min_se1 - s2 + s1)

        for i in range(numTeams):
            for j in range(numTeams):
                for s1 in range(numSlots):
                    for s2 in range(s1,numSlots):
                        if s1 != s2:
                            prod_SE1[l,i,j,s1,s2] = solver.NumVar(0,k_min_se1,'prod_SE1[{0}][{1}][{2}][{3}][{4}]'.format(s2,s1,j,i,l))
                            solver.Add(prod_SE1[l,i,j,s1,s2]<=k_min_se1*y[i,j,s1,s2])
                            solver.Add(prod_SE1[l,i,j,s1,s2]<=D_SE1[l,s1,s2])
                            solver.Add(prod_SE1[l,i,j,s1,s2] >=D_SE1[l,s1,s2]-k_min_se1*(1-y[i,j,s1,s2]))
                            if type_ == "HARD":
                                solver.Add(prod_SE1[l,i,j,s1,s2]==0)
                            else: 
                                objective.SetCoefficient(prod_SE1[l,i,j,s1,s2],penalty_se1)                    
   


# # Fairness Constraints

# # FA2

D_FA2 = {}
diff_FA2 = {}
SeparationConstraints = constraints.getElementsByTagName("FairnessConstraints")[0]
FA2_constraints = SeparationConstraints.getElementsByTagName("FA2")
for l,FA2_constraint in enumerate(FA2_constraints):
    intp = int(FA2_constraint.getAttribute("intp"))
    mode = FA2_constraint.getAttribute("mode")
    penalty = int(FA2_constraint.getAttribute("penalty"))
    slots_FA2_org = FA2_constraint.getAttribute("slots").split(';')
    team_FA2 = FA2_constraint.getAttribute("teams").split(';')
    type_FA2 = FA2_constraint.getAttribute("type")
    for slots_FA2_str in slots_FA2_org:
        slots_FA2 = list(range(int(slots_FA2_str)+1))
        for i in team_FA2:
            for j in team_FA2:
                D_FA2[slots_FA2[-1],int(i),int(j)] = solver.NumVar(0,solver.infinity(),'D_FA2[{0}][{1}][{2}]'.format(slots_FA2[-1],int(j),int(i)))
                diff_FA2[slots_FA2[-1],int(i),int(j)] = solver.NumVar(0,solver.infinity(),'diff_FA2[{0}][{1}][{2}]'.format(slots_FA2[-1],int(j),int(i)))
                home_i = solver.Sum([home[int(i),int(s)] for s in slots_FA2])
                home_j = solver.Sum([home[int(j),int(s)] for s in slots_FA2])
                solver.Add(diff_FA2[slots_FA2[-1],int(i),int(j)] >= home_i-home_j)
                solver.Add(diff_FA2[slots_FA2[-1],int(i),int(j)] >= home_j-home_i)            
                solver.Add(D_FA2[slots_FA2[-1],int(i),int(j)] >= diff_FA2[slots_FA2[-1],int(i),int(j)] -intp)
                if type_FA2=="HARD":
                    solver.Add(D_FA2[slots_FA2[-1],int(i),int(j)] ==0)
                else:
                    objective.SetCoefficient(D_FA2[slots_FA2[-1],int(i),int(j)],penalty)


# solver.Minimize(0)
objective.SetMinimization()


status = solver.Solve()
end_time = time.perf_counter()

for s in range(numSlots):
    for i in range(numTeams):
        for j in range(numTeams):  
            if X[i,j,s].solution_value() == 1.0:
                print("s = ",s," i = ",i,"j = ",j," val = ",X[i,j,s].solution_value())


for s in range(numSlots):
    for i in range(numTeams):
        for j in range(numTeams): 
            for h in range(2):
                if H[i,j,s,h].solution_value() == 1.0:
                    if (h == 0):
                        print("s = ",s," i = ",i,"j = ",j," h = ",h," val = ",H[i,j,s,h].solution_value())


objectiveVal = defaultdict(int)


# ## CA1 D_Value


objectiveVal['CA1'] = 0
for i,constraintsSet in enumerate(CA1_constraints):
    team_a = int(constraintsSet.getAttribute("teams"))
    slots_ = constraintsSet.getAttribute("slots").split(';')
    penalty_ = int(constraintsSet.getAttribute("penalty"))
    if D_CA1[i,team_a].solution_value() > 0:
        print("i : ",i," CA1 D VAlue : ",D_CA1[i,team_a].solution_value()," Slots :",slots_) 
        objectiveVal['CA1'] += (D_CA1[i,team_a].solution_value()*penalty_)


# ## CA2 D_Value

objectiveVal['CA2'] = 0
for i,constraintsSet in enumerate(CA2_constraints):
    team_1 = int(constraintsSet.getAttribute("teams1"))
    slots_ = constraintsSet.getAttribute("slots").split(';')
    penalty_ = int(constraintsSet.getAttribute("penalty"))
    if D_CA2[i,team_1].solution_value()>0:
        objectiveVal['CA2'] += (D_CA2[i,team_1].solution_value()*penalty_)
        print("i : ",i," CA2 D VAlue : ",D_CA2[i,team_1].solution_value()," Slots :",slots_) 


# ## CA3 D Value

objectiveVal['CA3'] = 0
for i,constraintsSet in enumerate(CA3_constraints):
    intp = int(constraintsSet.getAttribute("intp"))
    team_1 = (constraintsSet.getAttribute("teams1")).split(';')
    team_2 = (constraintsSet.getAttribute("teams2")).split(';')
    penalty_ = int(constraintsSet.getAttribute("penalty"))
    for t in team_1:
        t = int(t)    
        for l in range(numSlots - intp + 1):  
            if D_CA3[i,l,t].solution_value()>0:
                objectiveVal['CA3'] += (D_CA3[i,l,t].solution_value()*penalty_)
                print("i = {0} slot = {1} team = {2}".format(i,l,t)," CA3 D_VALUE ",D_CA3[i,l,t].solution_value(),"TEAMS 2 : ",team_2)


# ## CA4 D Value

objectiveVal['CA4'] = 0
for l,constraintsSet in enumerate(CA4_constraints):
    slots_ = constraintsSet.getAttribute("slots").split(';')
    team_1 = constraintsSet.getAttribute("teams1").split(';')
    team_2 = constraintsSet.getAttribute("teams2").split(';')
    max_ = int(constraintsSet.getAttribute("max"))
    min_ = int(constraintsSet.getAttribute("min"))
    mode2 = constraintsSet.getAttribute("mode2")
    type_ = constraintsSet.getAttribute("type")
    penalty_ = int(constraintsSet.getAttribute("penalty"))
    objectiveVal['CA4'] += (D_CA4[l].solution_value()*penalty_)
    if mode2 == "GLOBAL":
        if type_ == "HARD":
            adg = sum([H[int(i),int(j),int(slot),m].solution_value() for i in team_1 for j in team_2 for m in mod for slot in slots_])
            print("l = ",l,"CA4 D Val",D_CA4[l].solution_value(),"Check Value = ",adg," max = ",max_)


# ## GA1 D Value

objectiveVal['GA1'] = 0
for i,constraint_set in enumerate(GA1_constraints):    
    Groups = constraint_set.getAttribute("meetings").split(';')  
    penalty_ = int(constraint_set.getAttribute("penalty"))
    objectiveVal['GA1'] += (D_GA1[i].solution_value()*penalty_)
    print("i : ",i," GA1 D_VALUE ",D_GA1[i].solution_value(),"Groups  : ",Groups)


# ## BR1 D Value

objectiveVal['BR1'] = 0
for i,BR1_constraint in enumerate(BR1_constraints):
    slots_BR1 = BR1_constraint.getAttribute("slots").split(';')
    penalty_ = int(BR1_constraint.getAttribute("penalty"))
    objectiveVal['BR1'] += (D_BR1[i].solution_value()*penalty_)
    print("Slots : ",slots_BR1,"D Value ",D_BR1[i].solution_value())


# ## BR2 D Value

objectiveVal['BR2'] = 0
for i,BR2_constraint in enumerate(BR2_constraints):
    penalty_ = int(BR2_constraint.getAttribute("penalty"))
    objectiveVal['BR2'] += (D_BR2[i].solution_value()*penalty_)
    print("BR2 D Value ", D_BR2[i].solution_value())


# ## FA2 D Value

objectiveVal['FA2'] = 0
for l,FA2_constraint in enumerate(FA2_constraints):
    intp = int(FA2_constraint.getAttribute("intp"))
    mode = FA2_constraint.getAttribute("mode")
    penalty = int(FA2_constraint.getAttribute("penalty"))
    slots_FA2_org = FA2_constraint.getAttribute("slots").split(';')
    team_FA2 = FA2_constraint.getAttribute("teams").split(';')
    type_FA2 = FA2_constraint.getAttribute("type")
    penalty_ = int(FA2_constraint.getAttribute("penalty"))
    for slots_FA2_str in slots_FA2_org:
        slots_FA2 = list(range(int(slots_FA2_str)+1))
        print(slots_FA2)
        for i in team_FA2:
            for j in team_FA2: 
                objectiveVal['FA2'] += (D_FA2[slots_FA2[-1],int(i),int(j)].solution_value()*penalty_)
                home_i = sum([home[int(i),int(s)].solution_value() for s in slots_FA2])
                home_j = sum([home[int(j),int(s)].solution_value() for s in slots_FA2])
                print("Slots = {0} Team_i = {1} home_i = {3} Team_j = {2} home_j = {4} val = ".format(slots_FA2[-1],int(i),int(j),home_i,home_j),D_FA2[slots_FA2[-1],int(i),int(j)].solution_value())


# ## SE1 D Value

objectiveVal['SE1'] = 0
if (boolPhase):
    for l,SE1_constraint in enumerate(SE1_constraints):
        k_min_se1 = int(SE1_constraint.getAttribute("min"))
        penalty_se1 = int(SE1_constraint.getAttribute("penalty"))
        type_ = SE1_constraint.getAttribute("type")
        penalty_ = int(SE1_constraint.getAttribute("penalty"))
        print(sum([prod_SE1[l,i,j,s1,s2].solution_value() if s1 != s2 else 0 for i in range(numTeams) for j in range(numTeams) for s1 in range(halfSlot) for s2 in range(halfSlot,numSlots) ]))
        for i in range(numTeams):
            for j in range(numTeams):
                for s1 in range(halfSlot):
                    for s2 in range(halfSlot,numSlots):
                        if s1 != s2:
                            if prod_SE1[l,i,j,s1,s2].solution_value() > 0:
                                objectiveVal['SE1'] += ((1+round(prod_SE1[l,i,j,s1,s2].solution_value()))*penalty_)
                                print("Team i = {0}, Team j ={1}, s1 = {2},s2 = {3} prod Val = ".format(i,j,s1,s2),prod_SE1[l,i,j,s1,s2].solution_value())
    objectiveVal['SE1'] /= 2
else:
    for l,SE1_constraint in enumerate(SE1_constraints):
        k_min_se1 = int(SE1_constraint.getAttribute("min"))
        penalty_se1 = int(SE1_constraint.getAttribute("penalty"))
        type_ = SE1_constraint.getAttribute("type")
        penalty_ = int(SE1_constraint.getAttribute("penalty"))
        print(sum([prod_SE1[l,i,j,s1,s2].solution_value() if s1 != s2 else 0 for i in range(numTeams) for j in range(numTeams) for s1 in range(numSlots) for s2 in range(s1,numSlots) ]))
        for i in range(numTeams):
            for j in range(numTeams):
                for s1 in range(numSlots):
                    for s2 in range(s1,numSlots):
                        if s1 != s2:
                            if prod_SE1[l,i,j,s1,s2].solution_value() > 0:
                                objectiveVal['SE1'] += ((1+round(prod_SE1[l,i,j,s1,s2].solution_value()))*penalty_)
                                print("Team i = {0}, Team j ={1}, s1 = {2},s2 = {3} prod Val = ".format(i,j,s1,s2),prod_SE1[l,i,j,s1,s2].solution_value())
    objectiveVal['SE1'] /= 2


# # Objective Value
objVal = str(sum(objectiveVal.values()))


from xml.etree.ElementTree import Element, SubElement, Comment
from xml.etree import ElementTree
from xml.dom import minidom

from datetime import date

solution = Element('Solution')
MetaData = SubElement(solution,'MetaData')
SolutionName = SubElement(MetaData,'SolutionName')
SolutionName.text = 'IP_Test.xml'
InstanceName = SubElement(MetaData,'InstanceName')
InstanceName.text = 'Test Instance 4.xml'
Contributor = SubElement(MetaData,'Contributor')
Contributor.text = 'Team ZERO'
Date = SubElement(MetaData,'Date',day=str(date.today().day),month=str(date.today().month),year=str(date.today().year))
SolutionMethod = SubElement(MetaData,'SolutionMethod')
SolutionMethod.text = 'IP'
ObjectiveValue = SubElement(MetaData,'objectiveValue',objective=objVal)
LowerBound = SubElement(MetaData,'LowerBound',objective=objVal,infeasibility="0")
Remarks = SubElement(MetaData,'Remarks')
Remarks.text = str(end_time - start_time)
Games = SubElement(solution,'Games')
for s in range(numSlots):
    for i in range(numTeams):
        for j in range(numTeams): 
            for h in range(2):
                if H[i,j,s,h].solution_value() == 1.0:
                    if (h == 0):
                        ScheduledMatch = SubElement(Games,'ScheduledMatch',home=str(i),away=str(j),slot=str(s))



xmlstr = minidom.parseString(ElementTree.tostring(solution)).toprettyxml(indent="  ")
with open(fileName[:-4]+'_solution.xml', "w") as f:
    f.write(xmlstr)





