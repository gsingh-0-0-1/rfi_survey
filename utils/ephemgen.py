import numpy as np

def flower_petal(center_az, center_el, n_petals, PATTERN_RADIUS, theta_step = 2 * np.pi / 250, invr = 2.55e-5):
    assert n_petals % 4 == 0
    k = int(n_petals / 2)

    theta_list = np.arange(0, 2 * np.pi, theta_step)
    r_list = PATTERN_RADIUS * np.cos(k * theta_list)

    az_list_cartesian = r_list * np.cos(theta_list)
    el_list_cartesian = r_list * np.sin(theta_list)

    center_x = (center_el - 90) * np.cos(center_az * np.pi / 180)
    center_y = (center_el - 90) * np.sin(center_az * np.pi / 180)

    az_list_cartesian += center_x
    el_list_cartesian += center_y

    az_list = np.pi + (np.arctan2(el_list_cartesian, az_list_cartesian))
    el_list = abs(90 - np.sqrt(az_list_cartesian ** 2 + el_list_cartesian ** 2))

    d_list = [0]
    t_list = [0]

    for ind in range(1, len(az_list)):
        d_list.append(np.arccos(np.cos(az_list[ind] - az_list[ind - 1]) * np.cos(el_list[ind] - el_list[ind - 1])))
        t_list.append(t_list[ind - 1] + d_list[ind] / 0.1)


    ephem = np.zeros((len(d_list), 4))
    ephem[:, 0] = np.array(t_list)
    ephem[:, 1] = np.array(az_list) * 180 / np.pi
    ephem[:, 2] = np.array(el_list)
    ephem[:, 3] = invr    

    return ephem


def raster_scan(center_az, center_el, az_radius, el_radius, interval = 0.2, invr = 2.55e-5):
    assert interval < az_radius
    assert interval < el_radius

    start_az = center_az - az_radius
    start_el = center_el - el_radius

    azlist = np.arange(start_az, start_az + 2 * az_radius + 0.01, interval)
    ellist = np.arange(start_el, start_el + 2 * el_radius + 0.01, interval)
    
    ephem = np.zeros((len(azlist) * len(ellist), 4))

    ephem_az = []
    ephem_el = []
    ephem_t = [n * interval for n in range(ephem.shape[0])]

    for ind in range(len(ellist)):
        ephem_el += [ellist[ind]]*len(azlist)
        azs = azlist
        if ind % 2 == 1:
            azs = azs[::-1]
        ephem_az += [az for az in azs]

    ephem = np.around(ephem, 5)

    ephem[:, 0] = ephem_t
    ephem[:, 1] = ephem_az
    ephem[:, 2] = ephem_el
    ephem[:, 3] = invr

    return ephem

