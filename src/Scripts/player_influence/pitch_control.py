"""
Pitch Control calculation module.

Provides functions for calculating pitch control surfaces.
"""

import sys
import os
import numpy as np

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import Metrica_PitchControl as mpc

from .config import Config


class PitchControlCalculator:
    """Handles pitch control calculations."""
    
    def __init__(self, gk_numbers, params=None, homeTeamStartLeft=True,
                 field_dimen=None, n_grid_cells_x=None, exclude_offside=False):
        """
        Initialize the pitch control calculator.
        
        Parameters
        ----------
        gk_numbers : list
            Goalkeeper jersey numbers [home_GK, away_GK]
        params : dict, optional
            Pitch control model parameters (default: mpc.default_model_params())
        homeTeamStartLeft : bool, optional
            If True, home team started left and attacks right (x > 0)
            If False, home team started right and attacks left (x < 0)
        """
        self.gk_numbers = gk_numbers
        self.params = params or mpc.default_model_params()
        self.homeTeamStartLeft = homeTeamStartLeft
        self.exclude_offside = exclude_offside
        self.field_dimen = field_dimen or Config.FIELD_DIMEN
        self.n_grid_cells_x = n_grid_cells_x or Config.N_GRID_CELLS_X
        if min(self.field_dimen) <= 0 or self.n_grid_cells_x < 4:
            raise ValueError('Positive pitch dimensions and at least four grid columns required')
        
        # Pre-calculate grid
        self._setup_grid()
    
    def _setup_grid(self):
        """Set up the pitch control grid."""
        field_dimen = self.field_dimen
        n_grid_cells_x = self.n_grid_cells_x
        n_grid_cells_y = int(n_grid_cells_x * field_dimen[1] / field_dimen[0])
        
        dx = field_dimen[0] / n_grid_cells_x
        dy = field_dimen[1] / n_grid_cells_y
        
        self.xgrid = np.arange(n_grid_cells_x) * dx - field_dimen[0]/2. + dx/2.
        self.ygrid = np.arange(n_grid_cells_y) * dy - field_dimen[1]/2. + dy/2.
        self.grid_shape = (len(self.ygrid), len(self.xgrid))
        self.cell_area_m2 = dx * dy
    
    def calculate_surface(self, home_row, away_row, attacking_half_only=True, attacking_team='Home'):
        """
        Calculate pitch control surface for given player positions.
        
        Parameters
        ----------
        home_row : Series
            Home team player position data
        away_row : Series
            Away team player position data
        attacking_half_only : bool
            If True, only calculate PC in the attacking half
        attacking_team : str
            'Home' or 'Away' - determines which half is the attacking half
            
        Returns
        -------
        tuple
            (PPCF_attacking, xgrid, ygrid)
        """
        ball_pos = np.array([home_row['ball_x'], home_row['ball_y']])
        
        PPCFa = np.zeros(shape=self.grid_shape)
        PPCFd = np.zeros(shape=self.grid_shape)
        
        # Role-dependent parameters must follow possession, not Home/Away labels.
        if attacking_team not in ('Home', 'Away'):
            raise ValueError('attacking_team must be Home or Away')
        rows = {'Home': home_row, 'Away': away_row}
        defending_team = 'Away' if attacking_team == 'Home' else 'Home'
        gks = dict(zip(('Home', 'Away'), map(str, self.gk_numbers)))
        attacking_players = mpc.initialise_players(
            rows[attacking_team], attacking_team, self.params, gks[attacking_team], is_attacking=True)
        defending_players = mpc.initialise_players(
            rows[defending_team], defending_team, self.params, gks[defending_team], is_attacking=False)
        if not attacking_players or not defending_players:
            raise ValueError('Both teams need at least one observed player')
        if self.exclude_offside:
            if len(defending_players) < 2:
                raise ValueError('Offside filtering needs at least two defenders')
            direction = (1 if self.homeTeamStartLeft else -1) * (1 if attacking_team == 'Home' else -1)
            line = max(0.0, direction * ball_pos[0], sorted(
                (direction*p.position[0] for p in defending_players), reverse=True)[1]) + 0.2
            attacking_players = [p for p in attacking_players if direction*p.position[0] <= line]
            if not attacking_players:
                raise ValueError('No onside attackers available')
        
        # Calculate pitch control at each grid location
        for ii in range(len(self.ygrid)):
            for jj in range(len(self.xgrid)):
                target_position = np.array([self.xgrid[jj], self.ygrid[ii]])
                
                # Only calculate in the attacking half
                if attacking_half_only:
                    if attacking_team == 'Home':
                        # If homeTeamStartLeft=True, home attacks right (x > 0), skip left half
                        # If homeTeamStartLeft=False, home attacks left (x < 0), skip right half
                        if self.homeTeamStartLeft and target_position[0] <= 0:
                            PPCFa[ii, jj] = np.nan
                            PPCFd[ii, jj] = np.nan
                            continue
                        elif not self.homeTeamStartLeft and target_position[0] >= 0:
                            PPCFa[ii, jj] = np.nan
                            PPCFd[ii, jj] = np.nan
                            continue
                    elif attacking_team == 'Away':
                        # If homeTeamStartLeft=True, away attacks left (x < 0), skip right half
                        # If homeTeamStartLeft=False, away attacks right (x > 0), skip left half
                        if self.homeTeamStartLeft and target_position[0] >= 0:
                            PPCFa[ii, jj] = np.nan
                            PPCFd[ii, jj] = np.nan
                            continue
                        elif not self.homeTeamStartLeft and target_position[0] <= 0:
                            PPCFa[ii, jj] = np.nan
                            PPCFd[ii, jj] = np.nan
                            continue
                
                PPCFa[ii, jj], PPCFd[ii, jj] = mpc.calculate_pitch_control_at_target(
                    target_position, attacking_players, defending_players, ball_pos, self.params
                )
        
        return PPCFa, self.xgrid, self.ygrid
    
    def calculate_surface_with_hybrid(self, home_row, away_row, attacking_team='Home',
                                       attacking_half_only=True):
        """
        Calculate pitch control with specified home/away rows.
        
        Parameters
        ----------
        home_row : Series
            Home team player position data
        away_row : Series
            Away team player position data
        attacking_team : str
            'Home' or 'Away'
        attacking_half_only : bool
            If True, only calculate in attacking half
            
        Returns
        -------
        tuple
            (PPCF, xgrid, ygrid)
        """
        return self.calculate_surface(home_row, away_row, attacking_half_only, attacking_team)
    
    @staticmethod
    def get_backfilled_row(tracking_data, frame):
        """
        Get row with backfilled velocities for pitch control calculation.
        
        Parameters
        ----------
        tracking_data : DataFrame
            Tracking data
        frame : int
            Frame number
            
        Returns
        -------
        Series
            Row with backfilled velocity data
        """
        return mpc._row_with_backfilled_velocities(tracking_data, frame)
