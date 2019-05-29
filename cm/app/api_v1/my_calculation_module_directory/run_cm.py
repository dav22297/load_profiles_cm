import os
import time
import sys
import numpy as np

from .dh_potential.CM_TUW4.polygonize import polygonize
from .dh_potential.CM_TUW0.rem_mk_dir import rm_mk_dir, rm_file
import dh_potential.CM_TUW4.district_heating_potential as DHP
import dh_potential.CM_TUW19.run_cm as CM19

from .excess_heat.excess_heat import excess_heat


def main(heat_density_map, pix_threshold, DH_threshold, output_raster1,
         output_raster2, output_shp1, output_shp2,
         search_radius, investment_period, discount_rate, cost_factor, operational_costs, transmission_line_threshold, nuts2_id, output_transmission_lines,
         in_orig=None, only_return_areas=False, ):
    # The CM can be run for the following ranges of pixel and Dh thresholds:
    if pix_threshold < 1:
        raise ValueError("Pixel threshold cannot be smaller than 1 GWh/km2!")
    if DH_threshold < 1:
        raise ValueError("DH threshold cannot be smaller than 1 GWh/year!")
    # DH_Regions: boolean array showing DH regions
    DH_Regions, geo_transform, total_heat_demand = DHP.DHReg(heat_density_map,
                                                             pix_threshold,
                                                             DH_threshold,
                                                             in_orig)
    if only_return_areas:
        geo_transform = None
        return DH_Regions
    DHPot, labels = DHP.DHPotential(DH_Regions, heat_density_map)
    total_potential = np.around(np.sum(DHPot),2)
    total_heat_demand = np.around(total_heat_demand, 2)

    CM19.main(output_raster1, geo_transform, 'int8', DH_Regions)
    CM19.main(output_raster2, geo_transform, 'int32', labels)
    polygonize(output_raster1, output_raster2, output_shp1, output_shp2, DHPot)
    rm_file(output_raster2, output_raster2[:-4] + '.tfw')

    total_excess_heat_available, total_excess_heat_connected, total_flow_scalar, total_cost_scalar, annual_cost_of_network, levelised_cost_of_heat_supply, excess_heat_profile, heat_demand_profile = \
        excess_heat(output_shp2, search_radius, investment_period, discount_rate, cost_factor, operational_costs, transmission_line_threshold, nuts2_id, output_transmission_lines)

    graphics = [
        {
                "type": "bar",
                "xLabel": "DH Area Label",
                "yLabel": "Potential (GWh/year)",
                "data": {
                        "labels": [str(x) for x in range(1, 1+len(DHPot))],
                        "datasets": [{
                                "label": "Potential in coherent areas",
                                "backgroundColor": ["#3e95cd"]*len(DHPot),
                                "data": list(np.around(DHPot,2))
                                }]
                }
            }, {
                "type": "bar",
                "xLabel": "",
                "yLabel": "Demand / Potential (GWh/year)",
                "data": {
                        "labels": ["Annual heat demand", "DH potential", "Total excess heat available",
                                   "Total excess heat from connected sites", "Excess heat used"],
                        "datasets": [{
                                "label": "Heat Demand Vs. Excess heat (GWh/year)",
                                "backgroundColor": ["#fe7c60", "#3e95cd"],
                                "data": [total_heat_demand, total_potential, total_excess_heat_available, total_excess_heat_connected, total_flow_scalar]
                                }]
                }
            }, {
             "type": "line",
                "xLabel": "",
                "yLabel": "Demand / Excess in MW",
                "data": {
                        "labels": [str(x) for x in range(8760)],
                        "datasets": [{
                                "label": "Excess heat",
                                "backgroundColor": ["#ff4000"],
                                "data": excess_heat_profile
                                },
                                {"label": "Heat demand",
                                "backgroundColor": ["#00bfff"],
                                "data": heat_demand_profile}
                        ]
                }
        }]
    return total_potential, total_heat_demand, graphics, total_excess_heat_available, total_excess_heat_connected, total_flow_scalar, total_cost_scalar, annual_cost_of_network, levelised_cost_of_heat_supply
    
    

if __name__ == "__main__":
    start = time.time()
    path = r'W:\workspace_mostafa\Hotmaps\Hotmaps\app\modules\common'
    data_warehouse = path + os.sep + 'AD/data_warehouse'
    heat_density_map = data_warehouse + os.sep + 'heat_tot_curr_density_AT.tif'
    output_dir = path + os.sep + 'Outputs'
    outRasterPath1 = output_dir + os.sep + 'F13_' + '1.tif'
    outRasterPath2 = output_dir + os.sep + 'F13_' + '2.tif'
    output_shp1 = output_dir + os.sep + 'F13_' + '1.shp'
    output_shp2 = output_dir + os.sep + 'F13_' + '2.shp'
    rm_mk_dir(output_dir)
    # pix_threshold [MWh/ha]
    pix_threshold = 100
    # DH_threshold [MWh/year]
    DH_threshold = 30000
    main(heat_density_map, pix_threshold, DH_threshold, outRasterPath1, outRasterPath2, output_shp1, output_shp2)
    elapsed = time.time() - start
    print("%0.3f seconds" % elapsed)
