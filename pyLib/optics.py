"""
This a basic python module for managing the lattice and optics, e.g.
   inspecting tune, chroma, twiss functions, phase spaces, etc...
"""


__version__ = '0.0'
__author__ = 'Angelos Efstratiou and Alessio Mereghetti'


import numpy as np
import matplotlib.pyplot as plt


def closest_stable_unstable(myLine, num_turns=1000, d_gen=0.0, xBoundary=3.5e-2, xSearch=[0, 1], absPrecisio=1e-6):
    """
    Identifies the two closest boundary points separating stable and 
    unstable regions around a given `xBoundary`.

    This function performs a binary search to find the stable and 
    unstable regions for a particle in the vicinity of `xBoundary`. 
    The search is done along the horizontal axis within the interval 
    defined by `xSearch`. The search continues until the difference 
    between the upper and lower bounds of `xSearch` is smaller than 
    a given precision (`absPrecisio`).

    Args:
        myLine: An XSuite line object.
        num_turns (int, optional): The number of turns (iterations) 
        to track the particle (default is 1000).
        d_gen (float, optional): The initial momentum deviation for 
        the particle (default is 0.0).
        xBoundary (float, optional): The boundary point in the 
        horizontal axis that separates stable and unstable regions 
        (default is 3.5e-2 m).
        xSearch (list, optional): The search interval for the boundary 
        on the horizontal axis, expressed as [x_min, x_max] 
        (default is [0, 1]).
        absPrecisio (float, optional): The absolute precision 
        threshold for stopping the search, expressed in meters 
        (default is 1e-6).

    Returns:
        list: A list representing the final search region `[x_min, x_max]` 
        that contains the boundary between stable and unstable regions.
    """

    while xSearch[1] - xSearch[0] > absPrecisio:
        
        # Generate a particle in the middle of the region
        x_test = (xSearch[0] + xSearch[1]) / 2
        p = myLine.build_particles(x=x_test, delta=d_gen)
        
        # Track
        myLine.track(p, num_turns=num_turns, turn_by_turn_monitor=True)
        rec_test = myLine.record_last_track
        
        # Update the search region
        if (rec_test.x > xBoundary).any():
            # Test particle is unstable
            # => Sepearatrix is on the right w.r.t x_test
            xSearch[1] = x_test
        else:
            # Test particle is stable
            # Sepearatrix is on the left w.r.t x_test
            xSearch[0] = x_test
            
    return xSearch
    
    
    
    
    
def record_separatrix(myLine, xSearch=[0,1], num_turns=1000, d_gen=0.0):
    """
    Tracks a particle at the outer edge of a narrowed-down search 
    region and returns its physical coordinates after each turn.

    This function generates a particle at the upper bound of the 
    `xSearch` interval and tracks it through multiple turns. 
    The coordinates of the particle are recorded at each turn.

    Args:
        myLine: An XSuite line object.
        xSearch (list, optional): The search region for the particle, 
        given as [x_min, x_max], where the particle is generated at `x_max` 
        (default is [0, 1]).
        num_turns (int, optional): The number of turns (iterations) 
        to track the particle (default is 1000).
        d_gen (float, optional): The initial momentum deviation 
        for the particle (default is 0.0).

    Returns:
        object: The recorded separatrix data from the last particle track,
        which contains the particle's physical coordinates at each turn.
    """

    # We track particles at the outer edge of narrowed-down search region
    p = myLine.build_particles(x=xSearch[1], delta=d_gen)
    myLine.track(p, num_turns=num_turns, turn_by_turn_monitor=True)

    rec_sep = myLine.record_last_track

    return rec_sep
    




def separatrix_at_septum(rec_sep, xBoundary=3.5e-2):
    """
    Analyzes the separatrix at the septum by finding the turn where 
    the particle was closest to the septum, performing a polynomial fit 
    at that point, and calculating the slope and px value at the septum.

    This function integrates the following steps:
    1. Finds the turn where the particle was closest to the septum.
    2. Fits a straight line (polynomial of degree 1) using the previous 
    and following passage.
    3. Calculates the slope of the separatrix at the septum.
    4. Calculates the px value at the septum using the polynomial fit.

    Args:
        rec_sep: turn-by-turn data at the separatrix.
        xBoundary (float, optional): The position of the septum, 
        defined in meters (default is 3.5e-2).

    Returns:
        dict: A dictionary called 'separatrix_results' containing:
        - 'slope': The slope of the separatrix at the septum.
        - 'px_at_septum': The px value at the septum.
        - 'closer_turn': The turn at which the particle was closer to the septum.
        - 'poly_sep': The array of coefficients of the best-fit straight line.
    """
    
    x_separ = rec_sep.x[0, :]
    px_separ = rec_sep.px[0, :]

    # Find the turn at which the particle was closer to the septum
    i_septum = np.argmin(np.abs(x_separ - xBoundary))
    
    # Fit a straight line using the previous and the following passage
    poly_sep = np.polyfit([x_separ[i_septum + 3], x_separ[i_septum - 3]],
                          [px_separ[i_septum + 3], px_separ[i_septum - 3]], deg=1)
    
    # Calculate the slope (derivative) of the polynomial
    slope = poly_sep[0]
    
    # Calculate the px value at the septum using the polynomial fit
    px_at_septum = np.polyval(poly_sep, xBoundary)
    
    # Name the dictionary for clarity
    separatrix_results = {
        'slope': slope,
        'px_at_septum': px_at_septum,
        'closer_turn': i_septum,
        'poly_sep': poly_sep 
    }
    
    return separatrix_results
    



    
def find_boundary_stable(myLine, xSearch, num_turns=1000, d_gen=0.0):
    """"
    Tracks a particle at the inner edge of a specified search region 
    and returns the turn-by-turn physical coordinates of the particle 
    as it evolves over the specified number of turns.

    This function tracks the motion of a particle that starts at the 
    inner edge of a narrowed-down search region (`xSearch[0]`) and 
    records its trajectory through the defined number of turns. 
    It is typically used to study the stability of the particle within 
    the search region.

    Args:
        myLine: An XSuite line object.
        xSearch (list of float): A two-element list [x_min, x_max] 
        that specifies the range of the search region in meters. 
        The particle is tracked starting at `xSearch[0]`.
        num_turns (int, optional): The number of turns to track the particle. 
        (default is 1000).
        d_gen (float, optional): The initial momentum deviation 
        for the particle (default is 0.0).

    Returns:
        object: The recorded trajectory data (turn-by-turn physical coordinates) 
        of the particle as it evolves over the specified number of turns.
    """
    # We track particles at the inner edge of narrowed-down search region 
    p = myLine.build_particles(x=xSearch[0], delta=d_gen)
    myLine.track(p, num_turns=num_turns, turn_by_turn_monitor=True)
    
    triangle = myLine.record_last_track
    
    return triangle



    
    
def sort_stable_boundary_coordinates(tbt_triang, nc_tbt_triang):
    """
    Sorts the boundary coordinates of a given triangular stable area 
    based on the angle (theta) of the normalized phase space coordinates.

    This function extracts boundary data from the `tbt_triang` and 
    `nc_tbt_triang` objects, computes the angle (theta) of the normalized 
    coordinates, sorts the data based on increasing theta, and returns 
    a dictionary containing the sorted arrays.

    Args:
        tbt_triang: An object containing the original phase space data.
        - tbt_triang.x: Array of x coordinates in the phase space.
        - tbt_triang.px: Array of px coordinates in the phase space.
        nc_tbt_triang: An object containing the normalized phase space data.
        - nc_tbt_triang.x_norm: Array of normalized x coordinates.
        - nc_tbt_triang.px_norm: Array of normalized px coordinates.

    Returns:
        dict: A dictionary containing the sorted boundary coordinates:
        - 'x_triang': Sorted x coordinates.
        - 'px_triang': Sorted px coordinates.
        - 'x_norm_triang': Sorted normalized x coordinates.
        - 'px_norm_triang': Sorted normalized px coordinates.
    """
    
    # Extract the necessary values from the inputs
    x_triang = tbt_triang.x[0, :]
    px_triang = tbt_triang.px[0, :]
    x_norm_triang = nc_tbt_triang.x_norm[0, :]
    px_norm_triang = nc_tbt_triang.px_norm[0, :]

    # Sort boundary coordinates with increasing theta
    theta_triang = np.angle(x_norm_triang + 1j * px_norm_triang)
    i_sorted = np.argsort(theta_triang)

    # Apply the sorting to all arrays
    sorted_coordinates = {
        'x_triang': x_triang[i_sorted],
        'px_triang': px_triang[i_sorted],
        'x_norm_triang': x_norm_triang[i_sorted],
        'px_norm_triang': px_norm_triang[i_sorted]
    }

    return sorted_coordinates





def find_fixed_points(tbt_triang, nc_tbt_triang, threshold=0.2):
    """
    This function finds three fixed points based on the particle's coordinates
    and momenta from a given triangular boundary of a stable area.

    Args:
        tbt_triang: Record object containing physical coordinates.
        nc_tbt_triang: Record object containing normalized coordinates.
        threshold (float, optional): Threshold for searching local maxima 
        (default is 0.2).

    Returns:
        dict: A dictionary containing:
        - 'x_norm_fp': Normalized x-coordinates of the fixed points.
        - 'px_norm_fp': Normalized px-coordinates of the fixed points.
        - 'x_fp': Physical x-coordinates of the fixed points.
        - 'px_fp': Physical px-coordinates of the fixed points.
    """
    
    # Combine x and px in complex form (normalized and physical space)
    z_triang_norm = nc_tbt_triang.x_norm[0, :] + 1j * nc_tbt_triang.px_norm[0, :]
    z_triang = tbt_triang.x[0, :] + 1j * tbt_triang.px[0, :]
    
    # Calculate amplitude (radius) in normalized space
    r_triang_norm = np.abs(z_triang_norm)

    # Find the index of the maximum amplitude (first fixed point)
    i_fp1 = np.argmax(r_triang_norm)
    z_fp1 = z_triang_norm[i_fp1]
    r_fp1 = np.abs(z_fp1)

    # Search for the local maximum amplitude at +/- 120 degrees from the first fixed point
    mask_fp2 = np.abs(z_triang_norm - z_fp1 * np.exp(1j * 2 / 3 * np.pi)) < threshold * r_fp1
    i_fp2 = np.argmax(r_triang_norm * mask_fp2)
    
    mask_fp3 = np.abs(z_triang_norm - z_fp1 * np.exp(-1j * 2 / 3 * np.pi)) < threshold * r_fp1
    i_fp3 = np.argmax(r_triang_norm * mask_fp3)

    # Build arrays with the fixed points in both physical and normalized space
    x_norm_fp = z_triang_norm[[i_fp1, i_fp2, i_fp3]].real
    px_norm_fp = z_triang_norm[[i_fp1, i_fp2, i_fp3]].imag
    x_fp = z_triang[[i_fp1, i_fp2, i_fp3]].real
    px_fp = z_triang[[i_fp1, i_fp2, i_fp3]].imag

    # Return the fixed points as a dictionary
    fixed_points = {
        'x_norm_fp': x_norm_fp,
        'px_norm_fp': px_norm_fp,
        'x_fp': x_fp,
        'px_fp': px_fp
    }

    return fixed_points
    




def plot_phase_space(rec_part, nc_part, rec_sep, nc_sep, poly_sep, sorted_tr, fixed_p, xBoundary=3.5e-2):
    """
    Plots the physical and normalized phase space trajectories 
    of a particle, the separatrix, the fitted line crossing the septum, 
    the boundary of the stable area, and the fixed points.

    Parameters:
    -----------
    rec_part : object
    An object containing the turn-by-turn data for a particle's physical coordinates. 
    Expected to have attributes `x` and `px`.
    
    nc_part : object
    An object containing the turn-by-turn data for a particle's normalized coordinates. 
    Expected to have attributes `x_norm` and `px_norm`.
    
    rec_sep : object
    An object containing the turn-by-turn data for the separatrix in physical coordinates.
    Expected to have attributes `x`, `px`, and `state` (indicating the state of the particle).
    
    nc_sep : object
    An object containing the turn-by-turn data for the separatrix in normalized coordinates.
    Expected to have attributes `x_norm` and `px_norm`.
    
    poly_sep : array
    The coefficients of the polynomial representing the fitted separatrix line at the septum.
    
    sorted_tr : dict
    A dictionary containing sorted boundary coordinates for the stable area, with keys:
    - `'x_norm_triang'`: Sorted normalized positions of the boundary.
    - `'px_norm_triang'`: Sorted normalized momenta of the boundary.
    - `'x_triang'`: Sorted physical positions of the boundary.
    - `'px_triang'`: Sorted physical momenta of the boundary.
    
    fixed_p : dict
    A dictionary containing the fixed points in both normalized and physical phase spaces, with keys:
    - `'x_norm_fp'`: Normalized positions of the fixed points.
    - `'px_norm_fp'`: Normalized momenta of the fixed points.
    - `'x_fp'`: Physical positions of the fixed points.
    - `'px_fp'`: Physical momenta of the fixed points.
    
    xBoundary : float, optional
    The position of the septum in meters (default is 3.5e-2 m).

    Returns:
    --------
    None
    The function generates and displays phase space plots but does not return any value.
    """
    
    # Create empty plots side by side
    plt.figure(figsize=(10, 5))
    ax_geom = plt.subplot(1, 2, 1, title='Physical phase space')
    ax_norm = plt.subplot(1, 2, 2, title='Normalized phase space')
    ax_geom.set_xlim(-5e-2, 5e-2); ax_geom.set_ylim(-5e-3, 5e-3)
    ax_norm.set_xlim(-15e-3, 15e-3); ax_norm.set_ylim(-15e-3, 15e-3)
    ax_norm.set_aspect('equal', adjustable='datalim')
    ax_geom.set_xlabel(r'${x} [m]$')
    ax_geom.set_ylabel(r'${p}_x$')
    ax_norm.set_xlabel(r'$\hat{x}$')
    ax_norm.set_ylabel(r'$\hat{p}_x$')
    plt.subplots_adjust(wspace=0.3)
    
    # Plot particles after each turn
    ax_geom.plot(rec_part.x.T, rec_part.px.T, '.', markersize=1, color='C0')
    ax_norm.plot(nc_part.x_norm.T, nc_part.px_norm.T, '.', markersize=1, color='C0')
    
    # Plot septum's position
    ax_geom.axvline(x=xBoundary, color='k', alpha=0.4, linestyle='--')
    
    # Overlap found separatrix
    mask_alive = rec_sep.state > 0

    for ii in range(3):
        ax_geom.plot(rec_sep.x[mask_alive][ii::3],
                     rec_sep.px[mask_alive][ii::3],
                     '-', lw=3, color='C1', alpha=0.9)
                     
        ax_norm.plot(nc_sep.x_norm[mask_alive][ii::3],
                     nc_sep.px_norm[mask_alive][ii::3],
                     '-', lw=3, color='C1', alpha=0.9)
    
    # Plot fitted line for the separatrix crossing the septum
    x_plt = [xBoundary - 1e-2, xBoundary + 1e-2]
    ax_geom.plot(x_plt, np.polyval(poly_sep, x_plt), '--k', linewidth=3)
    
    # Plot boundary of the stable area
    ax_norm.plot(sorted_tr['x_norm_triang'], sorted_tr['px_norm_triang'],
                     '-', lw=3, color='C2', alpha=0.9)
    ax_geom.plot(sorted_tr['x_triang'], sorted_tr['px_triang'], 
                     '-', lw=3, color='C2', alpha=0.9)
    
    # Plot fixed points
    ax_norm.plot(fixed_p['x_norm_fp'], fixed_p['px_norm_fp'], 
                    '*', markersize=10, color='k')
    ax_geom.plot(fixed_p['x_fp'], fixed_p['px_fp'], 
                    '*', markersize=10, color='k')
        
    
    
    
    
    
    
    
    
    
