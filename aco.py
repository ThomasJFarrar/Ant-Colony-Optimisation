import numpy as np
import xml.etree.ElementTree as ET
import copy
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

# Function to parse the XML file and retrieve the distance matrix
def get_distance_matrix(filename):
    # Parse the XML file
    tree = ET.parse(filename)
    root = tree.getroot()

    # Find the graph element
    graph_element = root.find('.//graph')

    # Find the number of vertices
    num_vertices = len(graph_element)

    # Initialize an empty matrix
    distance_matrix = np.zeros((num_vertices, num_vertices))

    # Fill the matrix with edge costs
    vertex_count = 0
    for vertex in graph_element:
        edges = vertex.findall('./edge')
        for edge in edges:
            target_vertex_index = int(edge.text)
            cost = edge.get('cost')
            distance_matrix[vertex_count, target_vertex_index] = cost
        vertex_count += 1

    return distance_matrix

# Function to initialize the heuristic matrix based on the distance matrix
def initialize_heuristic_matrix(distance_matrix, number_of_cities):
    heuristic_matrix = [[round(1 / distance_matrix[i][j], 4) if i != j else 0 for j in range(number_of_cities)] for i in range(number_of_cities)]
    return heuristic_matrix

# Function to initialize the pheromone matrix with random values
def initialize_pheromone_matrix(number_of_cities):
    pheromone_matrix = np.random.rand(number_of_cities, number_of_cities)
    # np.fill_diagonal(pheromone_matrix, 0)
    return pheromone_matrix

# Function to calculate transition probabilities based on pheromone and heuristic information
def calculate_transition_probabilities(pheromone_matrix, heuristic_matrix, current_city, number_of_cities, alpha, beta):
    probabilities = []

    for city in range(number_of_cities):
        pheromone = pheromone_matrix[current_city][city]
        heuristic = heuristic_matrix[current_city][city]

        probability = (pheromone ** alpha) * (heuristic ** beta)
        probabilities.append(probability)

    # Normalize probabilities to ensure they sum to 1
    total_probability = sum(probabilities)
    probabilities = [p / total_probability for p in probabilities]

    return probabilities

# Function to construct ant solutions
def construct_ant_solutions(heuristic_matrix, pheronome_matrix, number_of_cities, number_of_ants, alpha, beta):
    ant_solutions = []
    for ant in range(number_of_ants):
        ant_solution = []
        current_city = np.random.randint(number_of_cities)
        current_heuristic_matrix = copy.deepcopy(heuristic_matrix)
        for city in range(number_of_cities):
            ant_solution.append(current_city)
            for value in range(number_of_cities):
                current_heuristic_matrix[value][current_city] = 0
            probabilities = calculate_transition_probabilities(pheronome_matrix, current_heuristic_matrix, current_city, number_of_cities, alpha, beta)
            random_number = np.random.rand()
            cumulative_prob = 0
            for i, prob in enumerate(probabilities):
                cumulative_prob += prob
                if random_number <= cumulative_prob:
                    current_city = i
                    break
        ant_solutions.append(ant_solution)
    return ant_solutions

# Function to update pheromones in the environment
def update_pheromones(ant_solutions, pheromone_matrix, number_of_ants, number_of_cities, rho, q, global_best_solution):
    # Evaporation: Reduce all pheromone levels by a factor of rho
    pheromone_matrix *= (1 - rho)

    best_solution_cost = float('inf')
    best_solution_edges = None

    for ant_solution in ant_solutions:
        # Fitness of the ant solution is the inverse of the total distance
        fitness = 1 / sum(distance_matrix[ant_solution[i - 1], ant_solution[i]] for i in range(1, len(ant_solution)))

        # Pheromone update for each edge in the ant solution
        for i in range(len(ant_solution) - 1):
            city1, city2 = ant_solution[i], ant_solution[i + 1]
            delta_tau = q / fitness
            pheromone_matrix[city1, city2] += delta_tau
            pheromone_matrix[city2, city1] += delta_tau

        # Update global best solution
        total_cost = sum(distance_matrix[ant_solution[i - 1], ant_solution[i]] for i in range(1, len(ant_solution))) + distance_matrix[ant_solution[-1], ant_solution[0]]
        if total_cost < best_solution_cost:
            best_solution_cost = total_cost
            best_solution_edges = ant_solution.copy()

    # Deposit pheromone on the trail of the global best solution
    for i in range(len(best_solution_edges) - 1):
        city1, city2 = best_solution_edges[i], best_solution_edges[i + 1]
        pheromone_matrix[city1, city2] += q / best_solution_cost
        pheromone_matrix[city2, city1] += q / best_solution_cost

    return pheromone_matrix

# Function to perform Ant Colony Optimization
def aco(distance_matrix, number_of_cities, number_of_ants, alpha, beta, rho, q, num_runs):
    best_total_cost_aco = float('inf')
    best_solution_aco = None
    best_costs_aco = []

    best_total_cost_elitist = float('inf')
    best_solution_elitist = None
    best_costs_elitist = []

    for run in range(num_runs):
        print(f"\nRun {run + 1}/{num_runs}")

        # Normal ACO
        fitness_evaluations_aco = 0
        heuristic_matrix = initialize_heuristic_matrix(distance_matrix, number_of_cities)
        pheromone_matrix_aco = initialize_pheromone_matrix(number_of_cities)
        best_solution_aco_run = None
        best_total_cost_aco_run = float('inf')
        best_costs_aco_run = []

        while fitness_evaluations_aco < 10000:
            ant_solutions_aco = construct_ant_solutions(heuristic_matrix, pheromone_matrix_aco, number_of_cities, number_of_ants, alpha, beta)
            pheromone_matrix_aco = update_pheromones(ant_solutions_aco, pheromone_matrix_aco, number_of_ants, number_of_cities, rho, q, None)
            fitness_evaluations_aco += number_of_ants  # Update fitness evaluations based on the number of ants

            # Evaluate and store the best solution for the run
            for ant_solution in ant_solutions_aco:
                total_cost_aco = sum(distance_matrix[ant_solution[i - 1], ant_solution[i]] for i in range(1, len(ant_solution))) + distance_matrix[ant_solution[-1], ant_solution[0]]
                if total_cost_aco < best_total_cost_aco_run:
                    best_total_cost_aco_run = total_cost_aco
                    best_solution_aco_run = ant_solution
            best_costs_aco_run.append(best_total_cost_aco_run)

        # Elitist ACO
        fitness_evaluations_elitist = 0
        pheromone_matrix_elitist = initialize_pheromone_matrix(number_of_cities)
        best_solution_elitist_run = None
        best_total_cost_elitist_run = float('inf')
        best_costs_elitist_run = []

        while fitness_evaluations_elitist < 10000:
            ant_solutions_elitist = construct_ant_solutions(heuristic_matrix, pheromone_matrix_elitist, number_of_cities, number_of_ants, alpha, beta)
            pheromone_matrix_elitist = update_pheromones(ant_solutions_elitist, pheromone_matrix_elitist, number_of_ants, number_of_cities, rho, q, best_solution_elitist_run)
            fitness_evaluations_elitist += number_of_ants  # Update fitness evaluations based on the number of ants

            # Evaluate and store the best solution for the run
            for ant_solution in ant_solutions_elitist:
                total_cost_elitist = sum(distance_matrix[ant_solution[i - 1], ant_solution[i]] for i in range(1, len(ant_solution))) + distance_matrix[ant_solution[-1], ant_solution[0]]
                if total_cost_elitist < best_total_cost_elitist_run:
                    best_total_cost_elitist_run = total_cost_elitist
                    best_solution_elitist_run = ant_solution
            best_costs_elitist_run.append(best_total_cost_elitist_run)

        # Record the best results over runs for normal ACO
        if best_total_cost_aco_run < best_total_cost_aco:
            best_total_cost_aco = best_total_cost_aco_run
            best_solution_aco = best_solution_aco_run
            best_costs_aco = best_costs_aco_run

        # Record the best results over runs for elitist ACO
        if best_total_cost_elitist_run < best_total_cost_elitist:
            best_total_cost_elitist = best_total_cost_elitist_run
            best_solution_elitist = best_solution_elitist_run
            best_costs_elitist = best_costs_elitist_run

    # Print the final best solution and its total cost for normal ACO
    print("\nBest Solution (Normal ACO):", best_solution_aco)
    print("Best Total Cost (Normal ACO):", best_total_cost_aco)

    # Print the final best solution and its total cost for elitist ACO
    print("\nBest Solution (Elitist ACO):", best_solution_elitist)
    print("Best Total Cost (Elitist ACO):", best_total_cost_elitist)

    # Plot the graph for the best result of normal ACO
    plt.figure(figsize=(10, 5))  # Adjust the figsize parameter for a wider graph
    plt.plot(best_costs_aco, label='Normal ACO')
    caption_aco = "Best TSP Cost (Normal ACO, " + str(number_of_ants) + " ants, " + str(rho) + " evaporation rate): " + str(best_costs_aco[-1])
    plt.figtext(0.5, 0.5, caption_aco, wrap=True, horizontalalignment='center', fontsize=10, color='black')
    # Plot the graph for the best result of elitist ACO
    plt.plot(best_costs_elitist, label='Elitist ACO')
    caption_elitist = "Best TSP Cost (Elitist ACO, " + str(number_of_ants) + " ants, " + str(rho) + " evaporation rate): " + str(best_costs_elitist[-1])
    plt.figtext(0.5, 0.45, caption_elitist, wrap=True, horizontalalignment='center', fontsize=10, color='black')

    # Display the graph
    plt.xlabel('Iteration')
    plt.ylabel('Best TSP Cost')
    plt.title('Best TSP Cost vs Iteration')
    plt.legend()
    plt.show()

filename = "burma.xml"
distance_matrix = get_distance_matrix(filename)
number_of_cities = len(distance_matrix)

number_of_ants = 50
alpha = 1.0
beta = 2.0
rho = 0.5
q = 1.0

number_of_trials = 1
aco(distance_matrix, number_of_cities, number_of_ants, alpha, beta, rho, q, number_of_trials)
